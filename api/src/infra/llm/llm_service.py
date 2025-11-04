from __future__ import annotations

import json
from typing import Any
from typing import Dict
from typing import Optional

import google.generativeai as genai
from shared.logging import get_logger
from shared.settings import Settings

logger = get_logger(__name__)


class LLMService:
    """Service to interact with LLM (Gemini or Bedrock)"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.provider = settings.llm.provider.lower()
        self.model_name = settings.llm.model
        
        if self.provider == 'gemini':
            self._init_gemini()
        elif self.provider == 'bedrock':
            self._init_bedrock()
        else:
            logger.error(f'Unknown LLM provider: {self.provider}. Supported: gemini, bedrock')
            raise ValueError(f'Unsupported LLM provider: {self.provider}')
        
        logger.info(f'LLM initialized with provider: {self.provider}, model: {self.model_name}')
    
    def _init_gemini(self):
        """Initialize Google Gemini"""
        self.api_key = self.settings.llm.api_key
        
        if not self.api_key:
            logger.warning('Gemini API key not configured. LLM features will not work.')
        else:
            genai.configure(api_key=self.api_key)
    
    def _init_bedrock(self):
        """Initialize AWS Bedrock"""
        try:
            import boto3
            
            aws_config = {
                'region_name': self.settings.llm.aws_region,
            }
            
            if self.settings.llm.aws_access_key_id and self.settings.llm.aws_secret_access_key:
                aws_config['aws_access_key_id'] = self.settings.llm.aws_access_key_id
                aws_config['aws_secret_access_key'] = self.settings.llm.aws_secret_access_key
            
            self.bedrock_client = boto3.client('bedrock-runtime', **aws_config)
            logger.info(f'Bedrock initialized with region: {self.settings.llm.aws_region}')
        except ImportError:
            logger.error('boto3 not installed. Install it to use Bedrock: pip install boto3')
            raise
        except Exception as e:
            logger.error(f'Failed to initialize Bedrock: {e}')
            raise

    def _prepare_messages_for_gemini(self, messages: list[Dict[str, str]]) -> tuple[Optional[str], list[Dict[str, str]]]:
        """
        Extract system instruction and prepare messages for Gemini SDK
        
        Args:
            messages: List of message dicts with 'role' and 'content'
        
        Returns:
            Tuple (system_instruction, chat_messages)
        """
        system_instruction = None
        chat_messages = []
        
        for msg in messages:
            role = msg.get('role')
            content = msg.get('content', '')
            
            if role == 'system':
                # Gemini uses systemInstruction separately
                system_instruction = content
            elif role == 'user':
                chat_messages.append({
                    'role': 'user',
                    'parts': [content]
                })
            elif role == 'assistant':
                chat_messages.append({
                    'role': 'model',
                    'parts': [content]
                })
        
        return system_instruction, chat_messages

    def _prepare_messages_for_bedrock(self, messages: list[Dict[str, str]]) -> tuple[Optional[str], list[Dict[str, str]]]:
        """
        Extract system instruction and prepare messages for Bedrock
        
        Args:
            messages: List of message dicts with 'role' and 'content'
        
        Returns:
            Tuple (system_instruction, chat_messages)
        """
        system_instruction = None
        chat_messages = []
        
        for msg in messages:
            role = msg.get('role')
            content = msg.get('content', '')
            
            if role == 'system':
                system_instruction = content
            elif role in ['user', 'assistant']:
                chat_messages.append({
                    'role': role,
                    'content': content
                })
        
        return system_instruction, chat_messages

    async def _chat_completion_gemini(
        self,
        messages: list[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        response_format: Optional[str] = None,
    ) -> Optional[str]:
        """
        Call Google Gemini API for chat completion
        """
        if not self.api_key:
            logger.error('Gemini API key not configured')
            return None
            
        try:
            # Extract system instruction and messages
            system_instruction, chat_messages = self._prepare_messages_for_gemini(messages)
            
            # Add JSON instruction if needed
            if response_format == 'json_object' and system_instruction:
                system_instruction += "\n\nImportant: You MUST return the response as valid JSON only, without any markdown or other explanations."
            
            # Configure generation settings
            generation_config = genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )
            
            # Add response MIME type for JSON mode
            if response_format == 'json_object':
                generation_config.response_mime_type = 'application/json'
            
            
            model_kwargs = {
                'model_name': self.model_name,
                'generation_config': generation_config,
            }
            
            if system_instruction:
                model_kwargs['system_instruction'] = system_instruction
            
            model = genai.GenerativeModel(**model_kwargs)
            
            logger.debug(f'Calling Gemini model: {self.model_name}')
            
            # Call API using SDK
            # If there's chat history, use chat mode
            if len(chat_messages) > 1:
                # Use chat mode with history
                chat = model.start_chat(history=chat_messages[:-1])
                response = await chat.send_message_async(chat_messages[-1]['parts'][0])
            else:
                # Only 1 message, call directly
                response = await model.generate_content_async(
                    chat_messages[0]['parts'][0] if chat_messages else ""
                )
            
            # Extract text from response
            if response and response.text:
                logger.debug(f'Gemini response length: {len(response.text)} chars')
                return response.text
            else:
                logger.error('No content in Gemini response')
                return None
                    
        except Exception as e:
            logger.error(f'Gemini API call failed: {e}', exc_info=True)
            return None

    async def _chat_completion_bedrock(
        self,
        messages: list[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        response_format: Optional[str] = None,
    ) -> Optional[str]:
        """
        Call AWS Bedrock API for chat completion
        """
        try:
            system_instruction, chat_messages = self._prepare_messages_for_bedrock(messages)
            
            request_body = {
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': max_tokens,
                'temperature': temperature,
                'messages': chat_messages
            }
            
            if system_instruction:
                request_body['system'] = system_instruction
            
            # Add JSON instruction if needed
            if response_format == 'json_object':
                json_instruction = "\n\nImportant: You MUST return the response as valid JSON only, without any markdown or other explanations."
                if system_instruction:
                    request_body['system'] += json_instruction
                else:
                    request_body['system'] = json_instruction
            
            logger.debug(f'Calling Bedrock model: {self.model_name}')
            
            # Call Bedrock API
            response = self.bedrock_client.invoke_model(
                modelId=self.model_name,
                body=json.dumps(request_body)
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            
            if response_body.get('content'):
                content = response_body['content'][0].get('text', '')
                logger.debug(f'Bedrock response length: {len(content)} chars')
                return content
            else:
                logger.error('No content in Bedrock response')
                return None
                    
        except Exception as e:
            logger.error(f'Bedrock API call failed: {e}', exc_info=True)
            return None

    async def chat_completion(
        self,
        messages: list[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        response_format: Optional[str] = None,
    ) -> Optional[str]:
        """
        Call LLM API for chat completion (routes to appropriate provider)
        """
        if self.provider == 'gemini':
            return await self._chat_completion_gemini(messages, temperature, max_tokens, response_format)
        elif self.provider == 'bedrock':
            return await self._chat_completion_bedrock(messages, temperature, max_tokens, response_format)
        else:
            logger.error(f'Unknown provider: {self.provider}')
            return None

    async def structured_completion(
        self,
        messages: list[Dict[str, str]],
        temperature: float = 0.3,
    ) -> Optional[Dict[str, Any]]:
        """
        Call Gemini and parse JSON response
        
        Returns:
            Parsed JSON dict or None if error
        """
        response = await self.chat_completion(
            messages=messages,
            temperature=temperature,
            response_format='json_object',
        )
        
        if not response:
            return None
            
        try:
            # Gemini with responseMimeType='application/json' should return valid JSON
            # But still clean in case of markdown wrapping
            cleaned_response = response.strip()
            
            # Remove markdown code block markers if present
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]
            elif cleaned_response.startswith('```'):
                cleaned_response = cleaned_response[3:]
            
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            
            cleaned_response = cleaned_response.strip()
            
            # Parse JSON
            return json.loads(cleaned_response)
            
        except json.JSONDecodeError as e:
            logger.error(f'Failed to parse Gemini JSON response: {e}')
            logger.error(f'Response was: {response}')
            return None
