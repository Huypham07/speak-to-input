from __future__ import annotations

from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from domain.value_objects import StateType
from pydantic import BaseModel
from pydantic import Field


class BusinessState(BaseModel):
    """Business state in the state machine"""

    current: StateType
    previous: Optional[StateType] = None

    # Allowed state transitions from current state
    allowed_transitions: List[StateType] = Field(default_factory=list)

    # Context data accumulated through conversation
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description='Accumulated data from previous rounds',
    )

    def can_transition_to(self, target_state: StateType) -> bool:
        """Check if transition to target state is allowed"""
        return target_state in self.allowed_transitions
