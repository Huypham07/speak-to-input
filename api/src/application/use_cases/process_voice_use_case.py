from __future__ import annotations

from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from application.services import IntentUnderstandingInput
from application.services import IntentUnderstandingOutput
from application.services import IntentUnderstandingService
from application.services import StateMachineService
from application.services import VoiceService
from domain.entities import BusinessState
from domain.entities import Capability
from domain.plugins.registry import get_intent_plugin
from pydantic import BaseModel
from pydantic import Field
from shared.logging import get_logger
from shared.settings import Settings

logger = get_logger(__name__)


class VoiceProcessInput(BaseModel):
    session_id: str
    user_id: str

    # Input (at least one required)
    audio_data: Optional[str] = None

    # Context from frontend
    context: Dict[str, Any] = Field(default_factory=dict)


class ProcessVoiceUseCase:
    """
    Use case for processing voice input.

    1. Voice Processing (ASR + Normalization)
    2. Intent Understanding (Classification + Extraction)
    3. Orchestration:
       - Validation
       - Capability Resolution
       - State Management
       - Execution (when ready)

    This is the main entry point for all voice processing requests.
    """

    def __init__(
        self,
        settings: Settings,
        voice_service: VoiceService,
        intent_service: IntentUnderstandingService,
        state_machine_service: StateMachineService,
    ):
        self.settings = settings
        self.voice_service = voice_service
        self.intent_service = intent_service
        self.state_machine = state_machine_service

    async def execute(
        self,
        input: VoiceProcessInput,
    ) -> dict:
        """
        Execute the voice processing pipeline.

        Args:
            request: VoiceRequest from frontend

        Returns:
            Response dict with intent, capabilities, state
        """
        logger.info(f'Processing voice request: {input.session_id}')

        # Voice processing
        if input.audio_data:
            original_text, normalized_text, asr_confidence = \
                await self.voice_service.process(input.audio_data)
        else:
            raise ValueError('audio_data is required')

        logger.info(f'Normalized text: {normalized_text}')

        # Intent understanding
        intent_result = await self.intent_service.process(
            IntentUnderstandingInput(text=normalized_text),
        )

        logger.info(f'Classified intent: {intent_result.intent_type} (confidence: {intent_result.confidence})')

        # Get plugin for this intent
        plugin = get_intent_plugin(intent_result.intent_type.value)

        if not plugin:
            # Unknown intent
            return await self._handle_unknown_intent(
                input,
                intent_result,
            )

        capabilities: List[Capability] = []

        response = {
            'session_id': input.session_id,
            'intent_result': intent_result.model_dump(),
            'required_capabilities': [c.model_dump() for c in capabilities],
            'has_errors': False,
        }

        return response

    async def _handle_unknown_intent(
        self,
        input: VoiceProcessInput,
        intent_result: IntentUnderstandingOutput,
    ) -> dict:
        """Handle unknown intent"""
        from domain.value_objects import CapabilityType

        capabilities = [
            Capability(
                capability_type=CapabilityType.SHOW_ERROR,
                priority=1,
                data={
                    'message': 'Xin lỗi, tôi không hiểu yêu cầu của bạn.',
                    'suggestions': [
                        'Chuyển tiền',
                        'Kiểm tra số dư',
                        'Mở tài khoản',
                    ],
                },
            ),
        ]

        return {
            'session_id': input.session_id,
            'intent_result': intent_result.model_dump(),
            'required_capabilities': [c.model_dump() for c in capabilities],
            'has_errors': True,
            'error_message': 'Unknown intent',
        }
