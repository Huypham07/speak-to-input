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

from domain.value_objects import FieldStatus
from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator
from pydantic import ValidationError


class MissingFieldError(ValueError):
    """Trường bị thiếu hoặc None"""
    pass


class InvalidFieldError(ValueError):
    """Giá trị trường không hợp lệ"""
    pass


class AMBIGUOUSFieldError(ValueError):
    """Giá trị trường mô hồ"""
    pass


class FieldValidation(BaseModel):
    """Validation result for a single field"""

    field_name: str
    status: FieldStatus
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


def map_validation_errors(data: Dict[str, Any], model: Type[BaseModel]) -> List[FieldValidation]:
    validation_results: Dict[str, FieldValidation] = {}

    try:
        validated_data = model.model_validate(data)
        # Nếu không lỗi, toàn bộ đều VALID
        for field_name, value in validated_data.model_dump().items():
            validation_results[field_name] = FieldValidation(
                field_name=field_name,
                status=FieldStatus.VALID,
                value=value,
            )

    except ValidationError as e:
        error_fields = set()

        for err in e.errors():
            field_name = err['loc'][0]
            error_fields.add(field_name)

            error_message = err['msg']
            input_value = err.get('input')

            # get original error class
            exc_class = None
            if err.get('ctx') and 'error' in err['ctx']:
                exc_class = err['ctx']['error'].__class__.__name__

            # defaulr
            metadata = {'exc_class': exc_class}
            status = FieldStatus.INVALID
            # Gán theo loại lỗi,
            if exc_class == 'MissingFieldError':
                status = FieldStatus.MISSING
            elif exc_class == 'InvalidFieldError':
                status = FieldStatus.INVALID
            elif exc_class == 'AmbiguousFieldError':
                status = FieldStatus.AMBIGUOUS
                match = re.search(r'gợi ý: "([^"]+)"', error_message)
                if match:
                    suggested_category = match.group(1)
                    metadata['suggested_category'] = suggested_category

            elif err['type'] == 'missing':
                # pydantic catch
                status = FieldStatus.MISSING

            field_info = model.model_fields.get(field_name)
            if getattr(field_info, 'json_schema_extra', None):
                metadata['extra'] = field_info.json_schema_extra

            validation_results[field_name] = FieldValidation(
                field_name=field_name,
                status=status,
                value=input_value,
                error_message=error_message,
                metadata=metadata,
            )

        # the valid rest
        for field_name, value in data.items():
            if field_name not in error_fields:
                validation_results[field_name] = FieldValidation(
                    field_name=field_name,
                    status=FieldStatus.VALID,
                    value=value,
                )

    return list(validation_results.values())
