from __future__ import annotations

import base64
import time

import pytest
from application.services import VoiceService
from shared.settings import Settings


@pytest.mark.asyncio
async def test_speech_to_text_from_file():
    # Arrange
    #
    wav_path = 'F:\\Downloads\\sample.wav'
    with open(wav_path, 'rb') as f:
        audio_bytes = f.read()
    audio_data = base64.b64encode(audio_bytes).decode('utf-8')

    service = VoiceService(Settings())

    # load model by api, excute only one time
    await service.load_model('/opt/whisper.cpp/models/ggml-medium.bin')

    # Act
    start = time.time()
    text, confidence = await service.speech_to_text(audio_data)
    print(f"run for {time.time() - start}")
    # Assert
    assert isinstance(text, str)
    assert isinstance(confidence, float)
    assert confidence > 0.0
    print(f'✅ Output text: {text}')
# $env:PYTHONPATH="api/src"; pytest -v -s --maxfail=1 --disable-warnings
