from __future__ import annotations

from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from api.dependencies import get_orchestration_service
from api.dependencies import get_session_repository
from api.helpers.dependencies import get_current_user
from api.helpers.dependencies import get_current_user_optional
from api.helpers.jwt_auth import TokenData
from application.services.orchestration_service import OrchestrationInput
from application.services.orchestration_service import OrchestrationOutput
from application.services.orchestration_service import OrchestrationService
from fastapi import APIRouter
from fastapi import Depends
from infra.db.repositories import SessionRepository
from pydantic import BaseModel
from pydantic import Field

router = APIRouter(prefix='/speech', tags=['Speech to Input'])


class ProcessSpeechRequest(BaseModel):
    """Request to process speech input"""

    session_id: str = Field(..., description='Session ID for tracking conversation')
    text: str = Field(..., description='Transcribed text from ASR')
    is_confirmation: bool = Field(False, description='Whether this is a confirmation response')
    is_cancellation: bool = Field(False, description='Whether user wants to cancel')


class CapabilityResponse(BaseModel):
    """Capability response for frontend"""

    capability_type: str
    priority: int = 1
    data: Dict[str, Any] = Field(default_factory=dict)
    message: str | None = None
    requires: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProcessSpeechResponse(BaseModel):
    """Response from processing speech input"""

    session_id: str
    current_state: str
    intent: str | None = None
    intent_confidence: float = 0.0
    capabilities: List[CapabilityResponse] = Field(default_factory=list)
    message: str = ''
    parameters: Dict[str, Any] = Field(default_factory=dict)
    requires_confirmation: bool = False
    turn_count: int = 0


# TODO: Inject OrchestrationService through dependency injection
# For now, this is a placeholder


@router.post('/process', response_model=ProcessSpeechResponse)
async def process_speech_input(
    request: ProcessSpeechRequest,
    current_user: Optional[TokenData] = Depends(get_current_user_optional),
    orchestration_service: OrchestrationService = Depends(get_orchestration_service),
) -> ProcessSpeechResponse:
    """
    Process speech input through the orchestration pipeline:
    1. Intent Understanding
    2. State Machine Transition
    3. Plugin Execution

    This endpoint works for both authenticated and anonymous users.
    For authenticated users, user_id from JWT token is used.
    For anonymous users, session_id is used for tracking.

    This is the main endpoint for speech-to-input functionality.
    """

    # Get user_id from token if authenticated
    user_id = current_user.user_id if current_user else None

    # Create orchestration input
    orchestration_input = OrchestrationInput(
        session_id=request.session_id,
        user_id=user_id,
        text=request.text,
        is_confirmation=request.is_confirmation,
        is_cancellation=request.is_cancellation,
    )

    # Process through orchestration
    result = await orchestration_service.process(orchestration_input)

    # Convert to response
    return ProcessSpeechResponse(
        session_id=result.session_id,
        current_state=result.current_state.value,
        intent=result.intent.value if result.intent else None,
        intent_confidence=result.intent_confidence,
        capabilities=[
            CapabilityResponse(
                capability_type=cap.capability_type.value,
                priority=cap.priority,
                data=cap.data,
                message=cap.message,
                requires=cap.requires,
                metadata=cap.metadata,
            )
            for cap in result.capabilities
        ],
        message=result.message,
        parameters=result.parameters,
        requires_confirmation=result.requires_confirmation,
        turn_count=result.turn_count,
    )


@router.get('/session/{session_id}')
async def get_session(
    session_id: str,
    current_user: Optional[TokenData] = Depends(get_current_user_optional),
    session_repo: SessionRepository = Depends(get_session_repository),
):
    """
    Get session details by ID.
    Works for both authenticated and anonymous users.
    """
    session = await session_repo.get_by_session_id(session_id)

    if not session:
        return {'error': 'Session not found'}

    # Check ownership if authenticated
    if current_user and session.user_id != current_user.user_id:
        return {'error': 'Access denied'}

    return {
        'session_id': session.session_id,
        'current_state': session.current_state.value,
        'current_intent': session.current_intent.value if session.current_intent else None,
        'parameters': session.parameters,
        'turn_count': session.turn_count,
        'user_id': session.user_id,
    }


@router.delete('/session/{session_id}')
async def delete_session(
    session_id: str,
    current_user: Optional[TokenData] = Depends(get_current_user_optional),
    session_repo: SessionRepository = Depends(get_session_repository),
):
    """
    Delete/reset a session.
    Works for both authenticated and anonymous users.
    """
    session = await session_repo.get_by_session_id(session_id)

    if not session:
        return {'error': 'Session not found'}

    # Check ownership if authenticated
    if current_user and session.user_id != current_user.user_id:
        return {'error': 'Access denied'}

    await session_repo.delete(session_id)

    return {
        'session_id': session_id,
        'deleted': True,
    }
