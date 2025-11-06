from __future__ import annotations

import os
import tempfile

import aiohttp
from infra.llm.llm_service import LLMService
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

    def __init__(self, settings: Settings, llm_service: LLMService = None):
        self.settings = settings
        self.server_url = f'{settings.whisper.host}:{settings.whisper.port}'
        self.llm_service = llm_service or LLMService(settings)

    async def load_model(self, model_path: str):
        """Load model via /load endpoint before transcript"""
        async with aiohttp.ClientSession() as session:
            data = aiohttp.FormData()
            data.add_field('model', model_path)
            async with session.post(f'{self.server_url}/load', data=data) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    logger.error(f'Failed to load model: {text}')
                    return False
                logger.info(f'Model loaded: {model_path}')
                return True

    async def speech_to_text(self, audio_bytes: bytes) -> str:
        """
        Convert audio to text using ASR.

        Args:
            audio_data: Base64 encoded audio

        Returns:
            text
        """
    # Giữ file lại (delete=False) để có thể reopen
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_file.flush()
            tmp_path = tmp_file.name

        logger.info(f'Sending audio to server at {self.server_url}/inference')
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
                async with session.post(f'{self.server_url}/inference', data=data) as resp:
                    if resp.status != 200:
                        text = await resp.text()
                        logger.error(f'Inference failed: {text}')
                        return ''

                    ctype = resp.headers.get('Content-Type', '')
                    if 'json' in ctype:
                        result = await resp.json()
                        text = result.get('text', '')
                    else:
                        text = await resp.text()
                    logger.debug(f'Raw response:\n{text}')

                    return text
            finally:
                f.close()
                os.remove(tmp_path)

    async def normalize_text(self, text: str) -> str:
        """
        Normalize text for better intent understanding using LLM.

        Main normalization tasks:
        1. Convert Vietnamese number words to digits (e.g., "năm trăm nghìn" -> "500000")
        2. Convert abbreviated numbers (e.g., "5k" -> "5000", "2tr" -> "2000000")
        3. Standardize currency expressions to VND numbers
        4. Clean up and format the text

        Examples:
        - "năm trăm nghìn" -> "500000"
        - "2 triệu 5" -> "2500000"
        - "5k" -> "5000"
        - "1tr5" -> "1500000"

        Args:
            text: Raw text from ASR or user input

        Returns:
            Normalized text with numbers converted to digits
        """

        logger.info(f'Normalizing text: {text}')

        if not text or not text.strip():
            return text

        # Build system prompt for normalization
        system_prompt = """Bạn là trợ lý chuẩn hóa văn bản tiếng Việt, chuyên chuyển đổi các cách diễn đạt số tiền sang dạng số.

NHIỆM VỤ:
1. Chuyển đổi số tiền từ chữ sang số (VD: "năm trăm nghìn" -> "500000")
2. Xử lý các từ viết tắt: "k" = 1000, "tr" hoặc "triệu" = 1000000
3. Giữ nguyên các từ không phải số
4. Trả về câu đã chuẩn hóa, KHÔNG giải thích

QUY TẮC CHUYỂN ĐỔI SỐ TIỀN:
- "nghìn" = 1,000 (x1000)
- "k" = 1,000 (x1000)
- "triệu" = 1,000,000 (x1000000)
- "tr" = 1,000,000 (x1000000)
- "trăm nghìn" = 100,000
- "trăm k" = 100,000

VÍ DỤ:
Input: "chuyển cho mẹ năm trăm nghìn"
Output: "chuyển cho mẹ 500000"

Input: "thanh toán hóa đơn điện 2 triệu 5"
Output: "thanh toán hóa đơn điện 2500000"

Input: "gửi tiết kiệm 1tr5"
Output: "gửi tiết kiệm 1500000"

Input: "chuyển 50k cho anh"
Output: "chuyển 50000 cho anh"

Input: "tạo quỹ du lịch mục tiêu 10 triệu"
Output: "tạo quỹ du lịch mục tiêu 10000000"

CHÚ Ý:
- Luôn chuyển về số VND đầy đủ (không để "k" hoặc "triệu")
- Giữ nguyên cấu trúc câu, chỉ thay thế phần số
- Trả về ĐÚNG câu đã chuẩn hóa, không thêm giải thích hay markdown
"""

        user_message = f'Chuẩn hóa câu sau: "{text}"'

        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_message},
        ]

        try:
            # Call LLM for normalization
            normalized = await self.llm_service.chat_completion(
                messages=messages,
                temperature=0.1,  # Low temperature for consistent results
                max_tokens=500,
            )

            if normalized:
                normalized = normalized.strip()
                # Remove quotes if LLM wrapped the response
                if normalized.startswith('"') and normalized.endswith('"'):
                    normalized = normalized[1:-1]
                elif normalized.startswith("'") and normalized.endswith("'"):
                    normalized = normalized[1:-1]

                logger.info(f'Normalized: {text} -> {normalized}')
                return normalized
            else:
                logger.warning('LLM returned empty response, using original text')
                return text.lower().strip()

        except Exception as e:
            logger.error(f'Error normalizing text with LLM: {e}', exc_info=True)
            # Fallback to basic normalization
            return text.lower().strip()

    async def process(
        self,
        audio_bytes: bytes,
    ) -> tuple[str, str]:
        """
        Process audio input.

        Args:
            audio_bytes: Audio data in bytes

        Returns:
            (original_text, normalized_text)
        """
        # Step 1: ASR
        # asr_text = await self.speech_to_text(audio_bytes)

        # TEST MODE: Random test sentences for different intents
        import random

        test_sentences = [
            # Create Bill intent
            'tạo hóa đơn tiền điện năm trăm nghìn hạn mười hai tháng hai',
            'tạo bill tiền nước ba trăm nghìn hạn hai mươi tháng này',
            'thêm hóa đơn tiền internet bốn trăm nghìn danh mục tiện ích',
            'tạo hóa đơn tiền thuê nhà năm triệu hạn một tháng ba',
            'bill bảo hiểm hai triệu hạn mười lăm tháng hai',

            # Transfer intent
            'chuyển tiền cho mẹ một triệu',
            'chuyển năm trăm nghìn cho tài khoản 123456789',
            'transfer hai triệu cho anh Tuấn tài khoản 987654321',
            'gửi ba trăm nghìn cho chị Hoa',

            # Create Fund intent
            'tạo quỹ du lịch mười triệu',
            'tạo quỹ khẩn cấp hai mươi triệu mục tiêu ba tháng sau',
            'thêm quỹ tiết kiệm năm triệu hạn sáu tháng',
            'tạo fund giáo dục mười lăm triệu',

            # Deposit/Withdraw intent
            'nạp tiền năm trăm nghìn',
            'rút tiền một triệu',
            'deposit ba trăm nghìn',
            'withdraw hai triệu',

            # Pay Bill intent
            'thanh toán hóa đơn tiền điện',
            'trả bill tiền nước',
            'pay hóa đơn internet',
        ]

        asr_text = random.choice(test_sentences)
        logger.info(f'🎲 TEST MODE - Random sentence: {asr_text}')

        # Step 2: Normalize
        normalized = await self.normalize_text(asr_text)

        return asr_text, normalized
