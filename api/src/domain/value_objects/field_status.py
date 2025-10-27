from __future__ import annotations

from enum import Enum


class FieldStatus(str, Enum):
    """Status of a field validation"""

    VALID = 'valid'
    MISSING = 'missing'
    INVALID = 'invalid'
    AMBIGUOUS = 'ambiguous'
