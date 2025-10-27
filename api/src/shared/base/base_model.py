from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict


class CustomBaseModel(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        from_attributes=True,
    )
