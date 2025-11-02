from __future__ import annotations

import json
from typing import Any
from typing import Dict
from typing import Optional

import aiohttp
from shared.logging import get_logger
from shared.settings import Settings

logger = get_logger(__name__)


class LLMService:
    """Service to interact with Google Gemini LLM"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.api_key = settings.llm.api_key
        self.model = settings.llm.model
        self.base_url = settings.llm.base_url
        
        if not self.api_key:
            logger.warning('Gemini API key not configured. LLM features will not work.')
        
        logger.info(f'Gemini LLM initialized with model: {self.model}')

    def _format_messages_for_gemini(self, messages: list[Dict[str, str]]) -> Dict[str, Any]:
        """
        Convert OpenAI-style messages to Gemini format
        
        Args:
            messages: List of message dicts with 'role' and 'content'
        
        Returns:
            Gemini API request format
        """
        system_instruction = None
        contents = []
        
        for msg in messages:
            role = msg.get('role')
            content = msg.get('content', '')
            
            if role == 'system':
                # Gemini uses systemInstruction separately
                system_instruction = content
            elif role == 'user':
                contents.append({
                    'role': 'user',
                    'parts': [{'text': content}]
                })
            elif role == 'assistant':
                contents.append({
                    'role': 'model',
                    'parts': [{'text': content}]
                })
        
        return {
            'system_instruction': system_instruction,
            'contents': contents
        }

    async def chat_completion(
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
            # Convert messages to Gemini format
            formatted = self._format_messages_for_gemini(messages)
            system_instruction = formatted['system_instruction']
            contents = formatted['contents']
            
            # Build payload
            payload = {
                'contents': contents,
                'generationConfig': {
                    'temperature': temperature,
                    'maxOutputTokens': max_tokens,
                }
            }
            
            # Add system instruction if exists
            if system_instruction:
                # Add JSON instruction if needed
                if response_format == 'json_object':
                    system_instruction += "\n\nQuan trọng: Bạn PHẢI trả về response dưới dạng JSON hợp lệ và chỉ JSON, không có text markdown hay giải thích nào khác."
                
                payload['systemInstruction'] = {
                    'parts': [{'text': system_instruction}]
                }
            
            # For JSON mode, also add to generation config
            if response_format == 'json_object':
                payload['generationConfig']['responseMimeType'] = 'application/json'
            
            # Build API URL
            url = f'{self.base_url}/v1beta/models/{self.model}:generateContent?key={self.api_key}'
            
            logger.debug(f'Calling Gemini model: {self.model}')
            
            # Call Gemini API
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f'Gemini API error: {response.status} - {error_text}')
                        return None
                    
                    result = await response.json()
                    
                    # Extract text from response
                    candidates = result.get('candidates', [])
                    if candidates:
                        content = candidates[0].get('content', {})
                        parts = content.get('parts', [])
                        if parts:
                            text_content = parts[0].get('text', '')
                            logger.debug(f'Gemini response length: {len(text_content)} chars')
                            return text_content
                    
                    logger.error('No content in Gemini response')
                    return None
                    
        except Exception as e:
            logger.error(f'Gemini API call failed: {e}', exc_info=True)
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
