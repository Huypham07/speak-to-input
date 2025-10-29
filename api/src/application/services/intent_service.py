from __future__ import annotations

from typing import Any
from typing import Dict

from domain.value_objects.intent_type import IntentType
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

    def __init__(self, settings: Settings):
        self.settings = settings

    async def process(
        self,
        input: IntentUnderstandingInput,
    ) -> IntentUnderstandingOutput:
        """
        Classify user intent and extract parameters.

        Args:
            text: Normalized text from voice service
            context: Current context (user state, previous intents, etc.)

        Returns:
            IntentResult with classification and parameters
        """

        text = input.text
        context = input.context
        # TODO: Implement intent classification
        # - Use LLM (GPT, Claude, etc.) to:
        #   - Understand user intent
        #   - Extract parameters
        #   - Handle context from previous rounds
        # - Return structured result

        logger.info(f'Classifying intent for: {text}')

        # Placeholder: Parse simple patterns
        intent_type, parameters = await self._classify(text, context)

        return IntentUnderstandingOutput(
            intent_type=intent_type,
            confidence=1.0,
            parameters=parameters,
        )

    async def _classify(
        self,
        text: str,
        context: Dict[str, Any],
    ) -> tuple[IntentType, Dict[str, Any]]:

        # Default: unknown
        return IntentType.UNKNOWN, {}

    def _extract_params(self, text: str) -> Dict[str, Any]:
        """Extract parameters for transfer """
        # TODO: Use LLM to extract structured data
        # For now, return empty dict
        return {}

    async def extract_clarification_data(
        self,
        text: str,
        missing_fields: list,
        current_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Extract missing data from user's clarification response.

        Args:
            text: User's clarification input
            missing_fields: List of fields that were missing
            current_data: Already collected data

        Returns:
            Extracted data for missing fields
        """
        # TODO: Use LLM to extract specific fields from text
        # - Focus on missing_fields
        # - Consider current_data for context
        # - Return dict with extracted values

        logger.info(f'Extracting clarification data from: {text}')
        logger.info(f'Missing fields: {missing_fields}')

        # Placeholder
        return {}

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
        Check if user is switching to a new intent.

        Args:
            text: User's input
            current_intent: Currently active intent

        Returns:
            (is_different, new_intent, confidence)
        """
        # TODO: Use LLM to detect intent change
        # - Compare with current_intent
        # - Return if it's a new intent with confidence

        logger.info(f'Checking intent change. Current: {current_intent}, Text: {text}')

        # Placeholder: assume no change
        return False, current_intent, 1.0
