from __future__ import annotations

import json
from typing import Any
from typing import Dict
from typing import Optional

from domain.plugins.registry import IntentPluginRegistry
from domain.value_objects.intent_type import IntentType
from infra.llm.llm_service import LLMService
from shared.logging import get_logger
from shared.settings import Settings

logger = get_logger(__name__)


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
                param_descriptions.append(f'{param_name} ({param_type}, {requirement}): {param_desc}')

            params_str = '\n   '.join(param_descriptions) if param_descriptions else 'không có parameters'

            # Add to prompt
            prompt_parts.append(
                f'\n{idx}. {plugin.intent_type} - {plugin.display_name}',
            )
            if plugin.description:
                prompt_parts.append(f'   Mô tả: {plugin.description}')
            prompt_parts.append(f'   Parameters:\n   {params_str}')

        # Add UNKNOWN intent
        num_intents = len(plugins) + 1
        prompt_parts.append(f'\n{num_intents}. UNKNOWN - Không xác định được (dùng khi không match intent nào)')

        # Add general notes
        prompt_parts.append('\n\nCHÚ Ý:')
        prompt_parts.append("- Số tiền có thể viết: '500 nghìn', '5 triệu', '1.5 triệu', '500000'")
        prompt_parts.append('- Số tiền LUÔN lưu dưới dạng VND đầy đủ (ví dụ: 500000, không phải 500)')
        prompt_parts.append('- Người nhận có thể là tên, số tài khoản, hoặc mối quan hệ (mẹ, bố, anh, chị)')
        prompt_parts.append("- Trả về JSON với format: {\"intent\": \"INTENT_TYPE\", \"confidence\": 0.0-1.0, \"parameters\": {...}}")

        self.system_prompt = '\n'.join(prompt_parts)

        # Log the generated prompt for debugging
        logger.debug(f'Generated system prompt:\n{self.system_prompt}')

    async def extract_intent_and_params(
        self,
        text: str,
        form_data: Optional[Dict[str, Any]] = None,
        hint_intent_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Extract intent and parameters from text with optional form data and hint.

        Args:
            text: Input text to analyze
            form_data: Optional form data with existing parameters (when hint_intent_type is provided)
            hint_intent_type: Optional hint about the expected intent type

        Returns:
            Dict with 'intent_type', 'parameters', and 'confidence'
        """
        logger.info(f'Extracting intent and params from: "{text}"')
        if form_data:
            logger.info(f'Form data: {form_data}')
        if hint_intent_type:
            logger.info(f'Hint intent type: {hint_intent_type}')

        # Case 1: No hint intent type - classify normally
        if not hint_intent_type:
            context: Dict[str, Any] = {}
            if form_data:
                context['form_data'] = form_data

            intent_type, parameters, confidence = await self._classify(text, context)

            return {
                'intent_type': intent_type.value if isinstance(intent_type, IntentType) else intent_type,
                'parameters': parameters,
                'confidence': confidence,
            }

        # Case 2: Hint intent type provided - build context with hint and form_data
        form_data = form_data or {}

        # Get plugin for hint intent to know schema and determine missing fields
        plugin = self.plugin_registry.get_plugin(hint_intent_type)
        if not plugin:
            logger.warning(f'Plugin not found for intent: {hint_intent_type}, falling back to normal classification')
            intent_type, parameters, confidence = await self._classify(text, {})
            return {
                'intent_type': intent_type.value if isinstance(intent_type, IntentType) else intent_type,
                'parameters': parameters,
                'confidence': confidence,
            }

        # Get required fields from schema
        schema = plugin.get_parameter_schema()
        required_fields = schema.get('required', [])

        # Determine missing fields
        missing_fields = [field for field in required_fields if field not in form_data or form_data.get(field) is None]

        # Build context with all necessary info for system prompt
        context = {
            'hint_intent_type': hint_intent_type,
            'form_data': form_data,
            'missing_fields': missing_fields,
            'schema': schema,
        }

        # Use LLM to classify (system prompt will handle intent change check and missing params extraction)
        intent_type, parameters, confidence = await self._classify(text, context)

        # Check if intent changed
        if intent_type.value != hint_intent_type:
            # Intent changed - return new intent with all params
            logger.info(f'User changed intent from {hint_intent_type} to {intent_type.value}')
            return {
                'intent_type': intent_type.value if isinstance(intent_type, IntentType) else intent_type,
                'parameters': parameters,
                'confidence': confidence,
            }

        # Same intent - merge form_data with extracted parameters
        # Merge form_data (existing) with parameters (newly extracted missing fields)
        merged_parameters = {**form_data, **parameters}

        logger.info(f'Extracted missing params for {hint_intent_type}, merged with existing data')
        logger.info(f'Existing: {form_data}, New: {parameters}, Merged: {merged_parameters}')

        return {
            'intent_type': hint_intent_type,
            'parameters': merged_parameters,  # Return merged form_data + new missing fields
            'confidence': confidence,
        }

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

        # Build system prompt based on context
        system_prompt = self._build_classify_prompt(context)

        # Build user message with context
        user_message = f"Phân tích lệnh: \"{text}\""
        if context:
            user_message += f'\n\nContext: {json.dumps(context, ensure_ascii=False)}'

        messages = [
            {'role': 'system', 'content': system_prompt},
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

    def _build_classify_prompt(self, context: Dict[str, Any]) -> str:
        """
        Build system prompt for classification based on context.

        If hint_intent_type is provided:
        - Check if user wants to change intent
        - If same intent: extract only missing params
        - If different intent: extract all params for new intent
        """
        hint_intent_type = context.get('hint_intent_type')
        form_data = context.get('form_data', {})
        missing_fields = context.get('missing_fields', [])
        schema = context.get('schema')

        # Base prompt
        prompt_parts = [self.system_prompt]

        # If hint_intent_type is provided, add special instructions
        if hint_intent_type:
            prompt_parts.append('\n\n=== TÌNH HUỐNG ĐẶC BIỆT ===')
            prompt_parts.append(f'Intent hiện tại đang được xử lý: {hint_intent_type}')
            prompt_parts.append(f'Dữ liệu đã có: {json.dumps(form_data, ensure_ascii=False)}')

            if missing_fields:
                # Build missing fields description
                properties = schema.get('properties', {}) if schema else {}
                missing_desc = []
                for field in missing_fields:
                    if field in properties:
                        field_info = properties[field]
                        field_desc = field_info.get('description', field)
                        field_type = field_info.get('type', 'any')
                        missing_desc.append(f'- {field} ({field_type}): {field_desc}')
                    else:
                        missing_desc.append(f'- {field}')

                prompt_parts.append('\nCác field còn thiếu cần extract:')
                prompt_parts.extend(missing_desc)

                prompt_parts.append('\nNHIỆM VỤ:')
                prompt_parts.append('1. Phân tích xem người dùng có đang muốn CHUYỂN SANG INTENT MỚI không:')
                prompt_parts.append('   - Nếu có: Trả về intent mới và TẤT CẢ parameters của intent mới')
                prompt_parts.append(f'   - Nếu không: Trả về intent hiện tại ({hint_intent_type}) và các parameters')
                prompt_parts.append('2. Parameters có thể là:')
                prompt_parts.append('   - Các field còn thiếu (missing_fields) - CẦN extract')
                prompt_parts.append('   - Các field đã có nhưng user muốn SỬA LẠI - CẦN extract giá trị mới')
                prompt_parts.append('3. Nếu user nói lại giá trị của field đã có (ví dụ: "không, 1 triệu nhé"), đó là muốn SỬA LẠI, hãy extract field đó với giá trị mới')
                prompt_parts.append('4. Nếu đã đủ tất cả parameters và user không muốn sửa gì, vẫn kiểm tra intent change nhưng có thể trả về empty parameters')
            else:
                prompt_parts.append('\nTất cả parameters đã đủ.')
                prompt_parts.append('NHIỆM VỤ:')
                prompt_parts.append('1. Phân tích xem người dùng có muốn CHUYỂN SANG INTENT MỚI không.')
                prompt_parts.append('   - Nếu có: Trả về intent mới và TẤT CẢ parameters')
                prompt_parts.append('   - Nếu không: Tiếp tục bước 2')
                prompt_parts.append('2. Phân tích xem người dùng có muốn SỬA LẠI parameters đã có không:')
                prompt_parts.append('   - Nếu user nói lại giá trị (ví dụ: "không, 1 triệu nhé" khi amount hiện tại là 500000): Hãy extract field đó với giá trị mới')
                prompt_parts.append(f'   - Nếu không muốn sửa: Trả về intent hiện tại ({hint_intent_type}) và empty parameters {{}}')
                prompt_parts.append('3. Nếu user muốn sửa, trả về các field được sửa với giá trị mới')

        return '\n'.join(prompt_parts)
