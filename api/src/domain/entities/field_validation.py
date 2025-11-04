from __future__ import annotations

import re
from datetime import date
from datetime import datetime
from typing import Annotated
from typing import Any
from typing import Dict
from typing import List
from typing import Literal
from typing import Optional
from typing import Type

from pydantic import BaseModel
from pydantic import Field


class FieldValidation(BaseModel):
    """Validation result for a single field"""

    field_name: str
    value: Optional[Any] = None
    error_message: Optional[str] = None
    metadata: dict = Field(default_factory=dict)


class ValidationResult(BaseModel):
    """Overall validation result for all fields"""

    is_valid: bool
    field_results: List[FieldValidation] = Field(default_factory=list)
    missing_fields: List[FieldValidation] = Field(default_factory=list)
    invalid_fields: List[FieldValidation] = Field(default_factory=list)
    ambiguous_fields: List[FieldValidation] = Field(default_factory=list)

    def get_field(self, field_name: str) -> Optional[FieldValidation]:
        """Get validation result for a specific field"""
        for field in self.field_results:
            if field.field_name == field_name:
                return field
        return None
