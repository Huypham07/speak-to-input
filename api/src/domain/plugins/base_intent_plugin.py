from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import Dict

from domain.entities import ExecutionResult


class IntentPlugin(ABC):
    """
    Base class for all intent plugins.
    Simplified for direct execution with inline validation.

    To add a new intent:
    1. Create a new file: {intent_name}_plugin.py
    2. Extend this class
    3. Implement all abstract methods
    4. Plugin will be auto-discovered on startup
    """

    @property
    @abstractmethod
    def intent_type(self) -> str:
        """Intent type identifier (e.g., 'SEND_MONEY')"""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable name"""
        pass

    @property
    def description(self) -> str:
        """Description of what this intent does"""
        return ''

    @property
    def requires_voice_confirmation(self) -> bool:
        """
        Whether this intent requires user confirmation when triggered by voice.
        Default is True for safety. Override to False for read-only intents.
        """
        return True

    # ========== Parameter Schema ==========

    @abstractmethod
    def get_parameter_schema(self) -> Dict[str, Any]:
        """
        Return JSON Schema defining required parameters.
        Used for validation and documentation.
        """
        pass

    # ========== Execution ==========

    @abstractmethod
    async def execute(
        self,
        parameters: Dict[str, Any],
        context: Dict[str, Any],
    ) -> ExecutionResult:
        """
        Execute the intent action with inline validation.

        Validates parameters and executes immediately.
        Returns clear errors if validation fails.

        Args:
            parameters: Parameters for execution
            context: Context including user_id and repositories

        Returns:
            ExecutionResult with success/failure and data
        """
        pass
