from __future__ import annotations

from enum import Enum


class StateType(str, Enum):
    """Business state types in the state machine"""

    # Initial
    INITIAL = 'initial'

    # In-progress states
    AWAITING_CLARIFICATION = 'awaiting_clarification'
    AWAITING_CONFIRMATION = 'awaiting_confirmation'
    READY = 'ready'
    EXECUTING = 'executing'

    # Terminal states
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'
