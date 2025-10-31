from __future__ import annotations

from enum import Enum


class StateType(str, Enum):
    """Business state types in the state machine"""

    # Initial state
    IDLE = 'IDLE'

    # Intent processing states
    INTENT_CLASSIFIED = 'INTENT_CLASSIFIED'
    VALIDATING = 'VALIDATING'

    # Clarification states
    CLARIFYING = 'CLARIFYING'
    DISAMBIGUATING = 'DISAMBIGUATING'

    # Confirmation states
    AWAITING_CONFIRMATION = 'AWAITING_CONFIRMATION'

    # Execution states
    EXECUTING = 'EXECUTING'

    # Terminal states
    COMPLETED = 'COMPLETED'
    FAILED = 'FAILED'
    CANCELLED = 'CANCELLED'
