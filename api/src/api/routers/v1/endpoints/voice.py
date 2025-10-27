from __future__ import annotations

from api.dependencies import get_process_voice_use_case
from api.schemas import VoiceProcessRequest
from api.schemas import VoiceProcessResponse
from application.use_cases import ProcessVoiceUseCase
from application.use_cases import VoiceProcessInput
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from shared.logging import get_logger

logger = get_logger(__name__)

voice_router = APIRouter(prefix='/voice', tags=['voice'])


@voice_router.post('/process', response_model=VoiceProcessResponse)
async def process_voice_input(
    request: VoiceProcessRequest,
    use_case: ProcessVoiceUseCase = Depends(get_process_voice_use_case),
):
    """
    Process voice input.

    This endpoint handles:
    - Initial voice input (new session or existing session)
    - Continuation of multi-round conversation
    - Clarification when user provides missing data
    - Confirmation when user approves/cancels action

    Flow:
    1. Frontend sends audio (base64) or text with session context
    2. Backend processes through pipeline:
       - ASR + Normalization (if audio)
       - Intent Classification
       - Orchestration:
            - Validation
            - Capability Resolution
            - State Management
    3. Returns capabilities for frontend to execute

    Multi-round conversation:
    - session_id tracks conversation context
    - context contains all previous interactions
    - Backend accumulates state across requests
    """
    try:
        # Convert to domain entity
        voice_request = VoiceProcessInput(**request.model_dump())

        # Process through use case
        result = await use_case.execute(voice_request)

        return VoiceProcessResponse(**result)

    except Exception as e:
        logger.error(f'Error processing voice input: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
