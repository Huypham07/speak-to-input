from __future__ import annotations

from enum import Enum


class CapabilityType(str, Enum):
    """Frontend capabilities that backend can request"""

    # Input/Clarification capabilities
    REQUEST_INPUT = 'REQUEST_INPUT'
    REQUEST_CONFIRMATION = 'REQUEST_CONFIRMATION'
    SHOW_OPTIONS = 'SHOW_OPTIONS'

    # Display capabilities
    SHOW_FORM = 'SHOW_FORM'
    SHOW_RESULT = 'SHOW_RESULT'
    SHOW_SUCCESS = 'SHOW_SUCCESS'
    SHOW_ERROR = 'SHOW_ERROR'
    SHOW_LOADING = 'SHOW_LOADING'

    # Navigation capabilities
    NAVIGATE = 'NAVIGATE'

    # Action capabilities
    EXECUTE_ACTION = 'EXECUTE_ACTION'
