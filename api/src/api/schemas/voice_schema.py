from __future__ import annotations

from typing import Any
from typing import Dict
from typing import Literal

from pydantic import BaseModel


# ========== WebSocket Message Types ==========


class VoiceInitMessage(BaseModel):
    """Initial message to start voice session"""

    type: Literal['init'] = 'init'
    intent_type: str
    form_data: Dict[str, Any] = {}


class VoiceAudioChunkMessage(BaseModel):
    """Audio chunk from microphone"""

    type: Literal['audio_chunk'] = 'audio_chunk'
    audio: str  # Base64 encoded audio data


class VoiceExecuteMessage(BaseModel):
    """Execute intent with parameters"""

    type: Literal['execute'] = 'execute'
    intent_type: str
    parameters: Dict[str, Any]
    needs_confirmation: bool = False


class VoiceConfirmMessage(BaseModel):
    """User confirmation for execution"""

    type: Literal['confirm'] = 'confirm'
    intent_type: str
    parameters: Dict[str, Any]


class VoicePingMessage(BaseModel):
    """Ping to keep connection alive"""

    type: Literal['ping'] = 'ping'


# ========== Server Response Types ==========


class VoiceConnectedResponse(BaseModel):
    """Connection established"""

    type: Literal['connected'] = 'connected'
    message: str


class VoiceInitAckResponse(BaseModel):
    """Session initialized"""

    type: Literal['init_ack'] = 'init_ack'
    message: str


class VoiceAudioAckResponse(BaseModel):
    """Audio chunk acknowledged"""

    type: Literal['audio_ack'] = 'audio_ack'
    message: str


class VoiceConfirmationRequiredResponse(BaseModel):
    """Confirmation required from user"""

    type: Literal['confirmation_required'] = 'confirmation_required'
    data: Dict[str, Any]
    message: str


class VoiceExecutionSuccessResponse(BaseModel):
    """Execution successful"""

    type: Literal['execution_success'] = 'execution_success'
    data: Dict[str, Any]
    message: str


class VoiceExecutionErrorResponse(BaseModel):
    """Execution failed"""

    type: Literal['execution_error'] = 'execution_error'
    error: str
    error_type: str
    data: Dict[str, Any] = {}


class VoiceErrorResponse(BaseModel):
    """General error"""

    type: Literal['error'] = 'error'
    error: str


class VoicePongResponse(BaseModel):
    """Pong response"""

    type: Literal['pong'] = 'pong'
