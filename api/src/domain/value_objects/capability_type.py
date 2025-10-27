from __future__ import annotations

from enum import Enum


class CapabilityType(str, Enum):
    """Frontend capabilities that backend can request"""

    # Input/Clarification
    REQUEST_FIELD = 'request_field'
    DISAMBIGUATE = 'disambiguate'

    # Display
    SHOW_RESULT = 'show_result'
    SHOW_ERROR = 'show_error'
    SHOW_LOADING = 'show_loading'
