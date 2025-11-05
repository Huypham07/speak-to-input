from __future__ import annotations

from typing import Any
from typing import Dict

from pydantic import BaseModel


class ExecutionResult(BaseModel):
    """Result of executing an intent"""
    success: bool
    message: str

    # Execution data
    data: Dict[str, Any] = {}
