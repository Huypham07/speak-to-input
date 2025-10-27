from __future__ import annotations

from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from pydantic import BaseModel
from pydantic import Field


class VoiceProcessRequest(BaseModel):
    """Request schema for processing voice input"""
    audio_data: Optional[str] = Field(
        None,
        description='Base64 encoded audio data',
    )

    # Session tracking
    session_id: str = Field(..., description='Session ID for conversation tracking')
    user_id: str = Field(..., description='User ID')

    # Context
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description='Current context from frontend',
    )


class VoiceProcessResponse(BaseModel):
    """Response schema for voice processing"""

    # Identifiers
    session_id: str

    # Intent result
    intent_result: Dict[str, Any]

    # Required capabilities for frontend
    required_capabilities: List[Dict[str, Any]] = Field(default_factory=list)

    # Errors
    has_errors: bool = False
    error_message: Optional[str] = None
