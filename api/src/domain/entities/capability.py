from __future__ import annotations

from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from domain.value_objects import CapabilityType
from pydantic import BaseModel
from pydantic import Field


class Capability(BaseModel):
    """Action that frontend needs to perform"""

    capability_type: CapabilityType
    priority: int = Field(default=1, description='Execution order')

    # Data for the capability
    data: Dict[str, Any] = Field(default_factory=dict)

    # Message to display to user
    message: Optional[str] = None

    # Dependencies on other capabilities
    requires: List[str] = Field(
        default_factory=list,
        description='Other capabilities that must complete first',
    )

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
