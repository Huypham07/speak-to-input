from __future__ import annotations

from datetime import datetime
from typing import Any
from typing import Dict
from typing import Optional

from domain.value_objects import IntentType
from domain.value_objects import StateType
from pydantic import BaseModel
from pydantic import Field


class Session(BaseModel):
    """
    Domain entity representing a conversation session.
    Tracks user interaction state across multiple requests.
    """

    session_id: str = Field(..., description='Unique session identifier')
    user_id: Optional[str] = Field(None, description='User ID if authenticated')

    # Current state
    current_state: StateType = Field(
        default=StateType.IDLE,
        description='Current state in the state machine',
    )
    previous_state: Optional[StateType] = Field(
        None,
        description='Previous state for rollback',
    )

    # Intent tracking
    current_intent: Optional[IntentType] = Field(
        None,
        description='Intent being processed',
    )
    intent_confidence: float = Field(
        default=0.0,
        description='Confidence score of intent classification',
    )

    # Accumulated data
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description='Accumulated context data from conversation',
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description='Extracted parameters for current intent',
    )

    # Metadata
    turn_count: int = Field(
        default=0,
        description='Number of conversation turns',
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description='Session creation time',
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description='Last update time',
    )
    expires_at: Optional[datetime] = Field(
        None,
        description='Session expiration time',
    )

    # Flags
    is_active: bool = Field(
        default=True,
        description='Whether session is active',
    )
    requires_confirmation: bool = Field(
        default=False,
        description='Whether current action requires user confirmation',
    )

    def update_state(self, new_state: StateType) -> None:
        """Update state with history tracking"""
        self.previous_state = self.current_state
        self.current_state = new_state
        self.updated_at = datetime.utcnow()

    def update_intent(self, intent: IntentType, confidence: float) -> None:
        """Update current intent"""
        self.current_intent = intent
        self.intent_confidence = confidence
        self.updated_at = datetime.utcnow()

    def update_parameters(self, parameters: Dict[str, Any]) -> None:
        """Merge new parameters with existing ones"""
        self.parameters.update(parameters)
        self.updated_at = datetime.utcnow()

    def update_context(self, context: Dict[str, Any]) -> None:
        """Merge new context with existing context"""
        self.context.update(context)
        self.updated_at = datetime.utcnow()

    def increment_turn(self) -> None:
        """Increment conversation turn counter"""
        self.turn_count += 1
        self.updated_at = datetime.utcnow()

    def reset(self) -> None:
        """Reset session to initial state"""
        self.current_state = StateType.IDLE
        self.previous_state = None
        self.current_intent = None
        self.intent_confidence = 0.0
        self.parameters = {}
        self.turn_count = 0
        self.requires_confirmation = False
        self.updated_at = datetime.utcnow()

    def is_expired(self) -> bool:
        """Check if session is expired"""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
