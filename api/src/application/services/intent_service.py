from __future__ import annotations

import json
from typing import Any
from typing import Dict

from domain.plugins.registry import IntentPluginRegistry
from domain.value_objects.intent_type import IntentType
from infra.llm.llm_service import LLMService
from pydantic import BaseModel
from pydantic import Field
from shared.logging import get_logger
from shared.settings import Settings

logger = get_logger(__name__)


class IntentUnderstandingInput(BaseModel):
    text: str
    context: Dict[str, Any] = {}


class IntentUnderstandingOutput(BaseModel):
    """Result of intent understanding"""

    intent_type: IntentType
    confidence: float = Field(..., ge=0.0, le=1.0)

    # Extracted parameters
    parameters: Dict[str, Any] = Field(default_factory=dict)


class IntentUnderstandingService:
    """
    Service for intent understanding:
    1. LLM preprocessing
    2. Intent classification
    3. Parameter extraction
    """

    def __init__(
        self,
        settings: Settings,
        llm_service: LLMService = None,
        plugin_registry: IntentPluginRegistry = None,
    ):
        self.settings = settings
        self.llm_service = llm_service or LLMService(settings)
        self.plugin_registry = plugin_registry

        # Build system prompt with available intents from registry
        self._build_system_prompt()

    def _build_system_prompt(self):
        """Build system prompt dynamically from plugin registry"""

        if not self.plugin_registry:
            raise ValueError('Plugin registry is required for IntentUnderstandingService')

        # Base prompt
        prompt_parts = [
            'Bạn là trợ lý AI tài chính thông minh, chuyên phân tích ý định của khách hàng từ lệnh giọng nói.\n',
            '\nCÁC INTENT HỖ TRỢ:',
        ]

        # Get plugins from registry
        plugins = self.plugin_registry.list_plugins()

        for idx, plugin in enumerate(plugins, start=1):
            # Get parameter schema
            schema = plugin.get_parameter_schema()
            properties = schema.get('properties', {})
            required_fields = schema.get('required', [])

            # Build parameter description
            param_descriptions = []
            for param_name, param_info in properties.items():
                is_required = param_name in required_fields
                param_desc = param_info.get('description', param_name)
                param_type = param_info.get('type', 'any')

                # Format: "field_name (type) - description [required/optional]"
                requirement = 'required' if is_required else 'optional'
                param_descriptions.append(f"{param_name} ({param_type}, {requirement}): {param_desc}")

            params_str = '\n   '.join(param_descriptions) if param_descriptions else 'không có parameters'

            # Add to prompt
            prompt_parts.append(
                f"\n{idx}. {plugin.intent_type} - {plugin.display_name}",
            )
            if plugin.description:
                prompt_parts.append(f"   Mô tả: {plugin.description}")
            prompt_parts.append(f"   Parameters:\n   {params_str}")

        # Add UNKNOWN intent
        num_intents = len(plugins) + 1
        prompt_parts.append(f"\n{num_intents}. UNKNOWN - Không xác định được (dùng khi không match intent nào)")

        # Add general notes
        prompt_parts.append('\n\nCHÚ Ý:')
        prompt_parts.append("- Số tiền có thể viết: '500 nghìn', '5 triệu', '1.5 triệu', '500000'")
        prompt_parts.append('- Số tiền LUÔN lưu dưới dạng VND đầy đủ (ví dụ: 500000, không phải 500)')
        prompt_parts.append('- Người nhận có thể là tên, số tài khoản, hoặc mối quan hệ (mẹ, bố, anh, chị)')
        prompt_parts.append("- Trả về JSON với format: {\"intent\": \"INTENT_TYPE\", \"confidence\": 0.0-1.0, \"parameters\": {...}}")

        self.system_prompt = '\n'.join(prompt_parts)

        # Log the generated prompt for debugging
        logger.debug(f"Generated system prompt:\n{self.system_prompt}")

    async def process(
        self,
        input: IntentUnderstandingInput,
    ) -> IntentUnderstandingOutput:
        """
        Classify user intent and extract parameters using LLM.

        Args:
            text: Normalized text from voice service
            context: Current context (user state, previous intents, etc.)

        Returns:
            IntentResult with classification and parameters
        """

        text = input.text
        context = input.context

        logger.info(f'Classifying intent for: {text}')

        # Use LLM to classify intent
        intent_type, parameters, confidence = await self._classify(text, context)

        return IntentUnderstandingOutput(
            intent_type=intent_type,
            confidence=confidence,
            parameters=parameters,
        )

    async def _classify(
        self,
        text: str,
        context: Dict[str, Any],
    ) -> tuple[IntentType, Dict[str, Any], float]:
        """
        Classify intent using LLM and extract parameters.

        Returns:
            (intent_type, parameters, confidence)
        """

        # Build user message with context
        user_message = f"Phân tích lệnh: \"{text}\""
        if context:
            user_message += f"\n\nContext: {json.dumps(context, ensure_ascii=False)}"

        messages = [
            {'role': 'system', 'content': self.system_prompt},
            {'role': 'user', 'content': user_message},
        ]

        # Call LLM
        result = await self.llm_service.structured_completion(messages, temperature=0.3)

        if not result:
            logger.warning('LLM returned no result, defaulting to UNKNOWN')
            return IntentType.UNKNOWN, {}, 0.0

        # Parse result
        try:
            intent_str = result.get('intent', 'UNKNOWN')
            confidence = float(result.get('confidence', 0.0))
            parameters = result.get('parameters', {})

            # Normalize amount if present (convert Vietnamese text to number)
            if 'amount' in parameters:
                parameters['amount'] = self._normalize_amount(parameters['amount'])

            # Convert intent string to enum
            try:
                intent_type = IntentType(intent_str)
            except ValueError:
                logger.warning(f'Unknown intent: {intent_str}')
                intent_type = IntentType.UNKNOWN
                confidence = 0.0

            logger.info(f'Classified: {intent_type.value} (confidence: {confidence:.2f})')
            logger.info(f'Parameters: {parameters}')

            return intent_type, parameters, confidence

        except Exception as e:
            logger.error(f'Failed to parse LLM result: {e}', exc_info=True)
            return IntentType.UNKNOWN, {}, 0.0

    def _normalize_amount(self, amount_value: Any) -> float:
        """
        Normalize amount from various formats to number.

        Examples:
            "500 nghìn" -> 500000
            "1.5 triệu" -> 1500000
            "500000" -> 500000
            500000 -> 500000
        """
        if isinstance(amount_value, (int, float)):
            return float(amount_value)

        if not isinstance(amount_value, str):
            return 0.0

        text = amount_value.lower().strip()

        # Extract number
        import re
        number_match = re.search(r'[\d.,]+', text)
        if not number_match:
            return 0.0

        number_str = number_match.group().replace(',', '.')
        try:
            base_number = float(number_str)
        except ValueError:
            return 0.0
        
        # Apply multiplier (VN + EN)
        text_no_space = text.replace(' ', '')

        thousand_markers = [
            'nghìn', 'nghin', 'k', 'thousand', 'ngàn', 'ngan'
        ]
        million_markers = [
            'triệu', 'trieu', 'm', 'million', 'mn', 'mil'
        ]

        if any(marker in text for marker in thousand_markers) or any(marker in text_no_space for marker in thousand_markers):
            return base_number * 1_000
        if any(marker in text for marker in million_markers) or any(marker in text_no_space for marker in million_markers):
            return base_number * 1_000_000

        return base_number

    async def extract_clarification_data(
        self,
        text: str,
        missing_fields: list,
        current_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Extract missing data from user's clarification response using LLM.

        Args:
            text: User's clarification input
            missing_fields: List of fields that were missing
            current_data: Already collected data

        Returns:
            Extracted data for missing fields
        """
        logger.info(f'Extracting clarification data from: "{text}"')
        logger.info(f'Missing fields: {missing_fields}')
        logger.info(f'Current data: {current_data}')

        # Build prompt
        system_prompt = """Bạn là trợ lý AI chuyên trích xuất thông tin từ câu trả lời của người dùng.

        Nhiệm vụ: Trích xuất các trường dữ liệu còn thiếu từ câu trả lời.

        CHÚ Ý:
        - Số tiền: "500 nghìn" -> 500000, "1.5 triệu" -> 1500000
        - Trả về JSON với các field được extract, không có field nào thì để {}
        - Chỉ trả về các field có trong danh sách missing_fields
        """

        user_message = f"""Dữ liệu hiện tại: {json.dumps(current_data, ensure_ascii=False)}
        Các field còn thiếu: {json.dumps(missing_fields, ensure_ascii=False)}
        Câu trả lời của user: "{text}"

        Hãy trích xuất các field còn thiếu từ câu trả lời. Trả về JSON format.
        """

        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_message},
        ]

        # Call LLM
        result = await self.llm_service.structured_completion(messages, temperature=0.2)

        if not result:
            logger.warning('LLM returned no result for clarification')
            return {}

        # Normalize amounts
        if 'amount' in result:
            result['amount'] = self._normalize_amount(result['amount'])

        logger.info(f'Extracted data: {result}')
        return result

    async def parse_confirmation(self, text: str) -> Dict[str, Any]:
        """
        Parse user's confirmation/cancellation response.

        Args:
            text: User's response text

        Returns:
            Dict with 'intent' (confirm/cancel/unclear) and optional details
        """
        # TODO: Use LLM or pattern matching to detect confirmation
        # - "có", "đồng ý", "ok", "yes" -> confirm
        # - "không", "hủy", "thôi", "cancel" -> cancel
        # - Others -> unclear

        logger.info(f'Parsing confirmation: {text}')

        text_lower = text.lower().strip()

        # Simple pattern matching (replace with LLM)
        if any(word in text_lower for word in ['có', 'đồng ý', 'ok', 'yes', 'được', 'ừ']):
            return {'intent': 'confirm'}
        elif any(word in text_lower for word in ['không', 'hủy', 'thôi', 'cancel', 'no']):
            return {'intent': 'cancel'}
        else:
            return {'intent': 'unclear'}

    async def check_intent_change(
        self,
        text: str,
        current_intent: str,
    ) -> tuple[bool, str, float]:
        """
        Check if user is switching to a new intent using LLM.

        Args:
            text: User's input
            current_intent: Currently active intent

        Returns:
            (is_different, new_intent, confidence)
        """
        logger.info(f'Checking intent change. Current: {current_intent}, Text: "{text}"')

        # Build prompt
        system_prompt = f"""Bạn là trợ lý AI phân tích xem người dùng có đang chuyển sang ý định mới hay không.

        Intent hiện tại: {current_intent}

        Nhiệm vụ: Xác định xem câu nói mới có phải là intent mới khác với intent hiện tại không.

        Trả về JSON:
        {{
        "is_different": true/false,
        "new_intent": "INTENT_TYPE" (nếu khác),
        "confidence": 0.0-1.0
        }}

        Ví dụ:
        - Current: SEND_MONEY, Text: "500 nghìn" -> is_different: false (đang cung cấp thông tin cho intent hiện tại)
        - Current: SEND_MONEY, Text: "Thôi để sau, xem số dư đi" -> is_different: true, new_intent: CHECK_BALANCE
        """

        user_message = f"""Intent hiện tại: {current_intent}
        Câu nói mới: "{text}"

        Người dùng có đang chuyển sang intent mới không?"""

        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_message},
        ]

        # Call LLM
        result = await self.llm_service.structured_completion(messages, temperature=0.2)

        if not result:
            logger.warning('LLM returned no result for intent change check')
            return False, current_intent, 1.0

        try:
            is_different = result.get('is_different', False)
            new_intent = result.get('new_intent', current_intent)
            confidence = float(result.get('confidence', 0.5))

            logger.info(f'Intent change: {is_different}, New: {new_intent}, Confidence: {confidence:.2f}')
            return is_different, new_intent, confidence

        except Exception as e:
            logger.error(f'Failed to parse intent change result: {e}')
            return False, current_intent, 1.0
