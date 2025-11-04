from __future__ import annotations

import base64
import os
import tempfile

import aiohttp
from shared.logging import get_logger
from shared.settings import Settings

logger = get_logger(__name__)


class VoiceService:
    """
    Service for voice processing:
    1. ASR (Automatic Speech Recognition)
    2. Text normalization
    3. Streaming ASR support
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self.server_url = f"{settings.whisper.host}:{settings.whisper.port}"

    async def load_model(self, model_path: str):
        """Load model via /load endpoint before transcript"""
        async with aiohttp.ClientSession() as session:
            data = aiohttp.FormData()
            data.add_field('model', model_path)
            async with session.post(f"{self.server_url}/load", data=data) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    logger.error(f"Failed to load model: {text}")
                    return False
                logger.info(f"Model loaded: {model_path}")
                return True

    async def speech_to_text(self, audio_bytes: bytes) -> tuple[str, float]:
        """
        Convert audio to text using ASR.

        Args:
            audio_data: Base64 encoded audio

        Returns:
            (text, confidence)
        """
    # Giữ file lại (delete=False) để có thể reopen
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_file.flush()
            tmp_path = tmp_file.name

        logger.info(f"Sending audio to server at {self.server_url}/inference")
        timeout = aiohttp.ClientTimeout(total=None)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            data = aiohttp.FormData()

            # 👇 giữ file mở cho đến khi request kết thúc
            f = open(tmp_path, 'rb')
            try:
                data.add_field('file', f, filename='audio.wav', content_type='audio/wav')
                data.add_field('temperature', '0.0')
                data.add_field('temperature_inc', '0.2')
                data.add_field('response_format', 'srt')
                async with session.post(f"{self.server_url}/inference", data=data) as resp:
                    if resp.status != 200:
                        text = await resp.text()
                        logger.error(f"Inference failed: {text}")
                        return '', 0.0

                    ctype = resp.headers.get('Content-Type', '')
                    if 'json' in ctype:
                        result = await resp.json()
                        text = result.get('text', '')
                        conf = result.get('confidence', 1.0)
                    else:
                        text = await resp.text()
                        conf = 1.0
                    logger.debug(f"Raw response:\n{text}")

                    return text, conf
            finally:
                f.close()
                os.remove(tmp_path)

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
        audio_bytes: bytes,
    ) -> tuple[str, str, float]:
        """
        Process audio input.

        Args:
            audio_data: Base64 encoded audio

        Returns:
            (original_text, normalized_text, confidence)
        """
        # Step 1: ASR
        asr_text, confidence = await self.speech_to_text(audio_bytes)

        # Step 2: Normalize
        normalized = await self.normalize_text(asr_text)

        return asr_text, normalized, confidence

    async def stream_asr(self, audio_chunk: str) -> str:
        """
        Process audio chunk for streaming ASR (partial transcript).

        This is used for real-time feedback during recording.

        Args:
            audio_chunk: Base64 encoded audio chunk

        Returns:
            Partial transcript text
        """
        # TODO: Implement streaming ASR

        logger.debug('Processing audio chunk for streaming ASR')

        return ''
