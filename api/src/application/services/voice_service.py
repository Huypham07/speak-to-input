from __future__ import annotations

from shared.logging import get_logger
from shared.settings import Settings

logger = get_logger(__name__)


class VoiceService:
    """
    Service for voice processing:
    1. ASR (Automatic Speech Recognition)
    2. Text normalization
    """

    def __init__(self, settings: Settings):
        self.settings = settings

    async def speech_to_text(self, audio_data: str) -> tuple[str, float]:
        """
        Convert audio to text using ASR.

        Args:
            audio_data: Base64 encoded audio

        Returns:
            (text, confidence)
        """
        # TODO: Implement ASR
        # - Decode base64 audio
        # - Call ASR service
        # - Return text and confidence

        logger.info('Processing audio with ASR')

        return '', 1.0

    async def normalize_text(self, text: str) -> str:
        """
        Normalize text for better intent understanding.

        Examples:
        - "năm trăm nghìn" -> "500000"
        - "2 triệu 5" -> "2500000"
        - "k" -> "000"

        Args:
            text: Raw text from ASR or user input

        Returns:
            Normalized text
        """

        logger.info(f'Normalizing text: {text}')

        normalized = text.lower().strip()

        return normalized

    async def process(
        self,
        audio_data: str,
    ) -> tuple[str, str, float]:
        """
        Process audio input end-to-end.

        Args:
            audio_data: Base64 encoded audio

        Returns:
            (original_text, normalized_text, confidence)
        """
        # Step 1: ASR
        asr_text, confidence = await self.speech_to_text(audio_data)

        # Step 2: Normalize
        normalized = await self.normalize_text(asr_text)

        return asr_text, normalized, confidence
