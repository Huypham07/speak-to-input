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
