from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import Dict
from typing import List

from domain.entities import BusinessState
from domain.entities import Capability
from domain.entities import ExecutionResult
from domain.entities import ValidationResult


class IntentPlugin(ABC):
    """
    Base class for all intent plugins.
    Each intent is a self-contained plugin with all its logic.

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

    # ========== Parameter Schema ==========

    @abstractmethod
    def get_parameter_schema(self) -> Dict[str, Any]:
        """
        Return JSON Schema defining required parameters.
        Used for validation and documentation.
        """
        pass

    # ========== Validation ==========

    @abstractmethod
    def validate_parameters(
        self,
        parameters: Dict[str, Any],
        context: Dict[str, Any],
    ) -> ValidationResult:
        """
        Validate extracted parameters.

        Args:
            parameters: Extracted parameters from intent understanding
            context: Current context (user data, state, etc.)

        Returns:
            ValidationResult with field-level validations
        """
        pass

    # ========== Capability Resolution ==========

    @abstractmethod
    def resolve_capabilities(
        self,
        parameters: Dict[str, Any],
        validation_result: ValidationResult,
        state: BusinessState,
    ) -> List[Capability]:
        """
        Determine what capabilities frontend needs to execute.

        This is where business logic maps to frontend actions.

        Args:
            parameters: Current parameters
            validation_result: Result from validate_parameters
            state: Current business state

        Returns:
            List of capabilities for frontend to execute
        """
        pass

    # ========== State Machine ==========

    # ========== Execution ==========

    @abstractmethod
    async def execute(
        self,
        parameters: Dict[str, Any],
        context: Dict[str, Any],
    ) -> ExecutionResult:
        """
        Execute the intent action.
        Called only after validation and confirmation (if needed).

        Args:
            parameters: Validated parameters
            context: Current context

        Returns:
            ExecutionResult with success/failure and data
        """
        pass
