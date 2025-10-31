from __future__ import annotations

from typing import Any
from typing import List
from typing import Optional

from domain.entities import BusinessState
from domain.entities import Capability
from domain.entities import Session
from domain.plugins.registry import get_intent_plugin
from domain.value_objects import CapabilityType
from domain.value_objects import IntentType
from domain.value_objects import StateType
from shared.logging import get_logger
from shared.settings import Settings

logger = get_logger(__name__)


class StateMachineService:
    """
    Service for managing business state machine.
    Handles state transitions and orchestrates the flow between states.
    """

    def __init__(self, settings: Settings):
        self.settings = settings

    def get_next_state(
        self,
        current_state: StateType,
        session: Session,
        validation_result: Optional[Any] = None,
    ) -> StateType:
        """
        Determine next state based on current state and validation result.

        State Machine Flow:
        IDLE -> INTENT_CLASSIFIED -> VALIDATING -> CONFIRMED -> EXECUTING -> COMPLETED -> IDLE
                                   |                          |
                                   -> CLARIFYING ------------>
                                   |
                                   -> FAILED -> IDLE
        """

        if current_state == StateType.IDLE:
            # After intent classification
            if session.current_intent and session.current_intent != IntentType.UNKNOWN:
                return StateType.INTENT_CLASSIFIED
            else:
                return StateType.FAILED

        elif current_state == StateType.INTENT_CLASSIFIED:
            # Move to validation
            return StateType.VALIDATING

        elif current_state == StateType.VALIDATING:
            # Check validation result
            if validation_result is None:
                return StateType.CLARIFYING

            if validation_result.is_valid:
                # Check if confirmation is needed
                if session.requires_confirmation:
                    return StateType.AWAITING_CONFIRMATION
                else:
                    return StateType.EXECUTING
            else:
                # Has missing or invalid fields
                if validation_result.missing_fields or validation_result.invalid_fields:
                    return StateType.CLARIFYING
                elif validation_result.ambiguous_fields:
                    return StateType.DISAMBIGUATING
                else:
                    return StateType.FAILED

        elif current_state == StateType.CLARIFYING:
            # After user provides more info, re-validate
            return StateType.VALIDATING

        elif current_state == StateType.DISAMBIGUATING:
            # After user selects an option, re-validate
            return StateType.VALIDATING

        elif current_state == StateType.AWAITING_CONFIRMATION:
            # User confirmed or rejected
            # This is handled by the orchestrator based on user response
            return StateType.EXECUTING  # If confirmed

        elif current_state == StateType.EXECUTING:
            # After execution
            return StateType.COMPLETED

        elif current_state == StateType.COMPLETED:
            # Reset to idle
            return StateType.IDLE

        elif current_state == StateType.FAILED:
            # Reset to idle
            return StateType.IDLE

        # Default: stay in current state
        return current_state

    def build_state_context(
        self,
        session: Session,
        validation_result: Optional[Any] = None,
    ) -> BusinessState:
        """
        Build business state with allowed transitions.
        """

        current_state = session.current_state
        allowed_transitions = self._get_allowed_transitions(current_state, session, validation_result)

        return BusinessState(
            current=current_state,
            previous=session.previous_state,
            allowed_transitions=allowed_transitions,
            context=session.context,
        )

    def _get_allowed_transitions(
        self,
        current_state: StateType,
        session: Session,
        validation_result: Optional[Any] = None,
    ) -> List[StateType]:
        """Get list of allowed state transitions from current state"""

        transitions = []

        if current_state == StateType.IDLE:
            transitions = [StateType.INTENT_CLASSIFIED, StateType.FAILED]

        elif current_state == StateType.INTENT_CLASSIFIED:
            transitions = [StateType.VALIDATING]

        elif current_state == StateType.VALIDATING:
            transitions = [
                StateType.EXECUTING,
                StateType.AWAITING_CONFIRMATION,
                StateType.CLARIFYING,
                StateType.DISAMBIGUATING,
                StateType.FAILED,
            ]

        elif current_state == StateType.CLARIFYING:
            transitions = [StateType.VALIDATING, StateType.FAILED]

        elif current_state == StateType.DISAMBIGUATING:
            transitions = [StateType.VALIDATING, StateType.FAILED]

        elif current_state == StateType.AWAITING_CONFIRMATION:
            transitions = [StateType.EXECUTING, StateType.IDLE, StateType.FAILED]

        elif current_state == StateType.EXECUTING:
            transitions = [StateType.COMPLETED, StateType.FAILED]

        elif current_state == StateType.COMPLETED:
            transitions = [StateType.IDLE]

        elif current_state == StateType.FAILED:
            transitions = [StateType.IDLE]

        return transitions

    def generate_capabilities(
        self,
        session: Session,
        validation_result: Any,
    ) -> List[Capability]:
        """
        Generate capabilities based on current state and validation.
        Capabilities tell the frontend what actions to take.
        """

        capabilities: list[Capability] = []

        # Get plugin for current intent
        if session.current_intent is None:
            return capabilities

        plugin = get_intent_plugin(session.current_intent.value)
        if plugin is None:
            logger.error(f'No plugin found for intent: {session.current_intent}')
            return capabilities

        # Build business state
        business_state = self.build_state_context(session, validation_result)

        # Let plugin resolve capabilities
        plugin_capabilities = plugin.resolve_capabilities(
            parameters=session.parameters,
            validation_result=validation_result,
            state=business_state,
        )

        capabilities.extend(plugin_capabilities)

        # Add state-specific capabilities
        if session.current_state == StateType.CLARIFYING:
            # Ask for missing fields
            if validation_result.missing_fields:
                for field in validation_result.missing_fields:
                    capabilities.append(
                        Capability(
                            capability_type=CapabilityType.REQUEST_INPUT,
                            data={
                                'field_name': field.field_name,
                                'field_type': 'text',  # TODO: Get from schema
                                'required': True,
                            },
                            message=f'Vui lòng cung cấp {field.field_name}',
                        ),
                    )

            # Report invalid fields
            if validation_result.invalid_fields:
                for field in validation_result.invalid_fields:
                    capabilities.append(
                        Capability(
                            capability_type=CapabilityType.SHOW_ERROR,
                            data={
                                'field_name': field.field_name,
                                'error_message': field.error_message,
                                'current_value': field.value,
                            },
                            message=field.error_message,
                        ),
                    )

        elif session.current_state == StateType.DISAMBIGUATING:
            # Show options for ambiguous fields
            if validation_result.ambiguous_fields:
                for field in validation_result.ambiguous_fields:
                    capabilities.append(
                        Capability(
                            capability_type=CapabilityType.SHOW_OPTIONS,
                            data={
                                'field_name': field.field_name,
                                'options': field.metadata.get('options', []),
                            },
                            message=f'Vui lòng chọn {field.field_name}',
                        ),
                    )

        elif session.current_state == StateType.AWAITING_CONFIRMATION:
            # Request confirmation
            capabilities.append(
                Capability(
                    capability_type=CapabilityType.REQUEST_CONFIRMATION,
                    data={
                        'intent': session.current_intent.value,
                        'parameters': session.parameters,
                    },
                    message='Vui lòng xác nhận thông tin',
                ),
            )

        elif session.current_state == StateType.COMPLETED:
            # Show success
            capabilities.append(
                Capability(
                    capability_type=CapabilityType.SHOW_SUCCESS,
                    data={
                        'intent': session.current_intent.value,
                    },
                    message='Thực hiện thành công',
                ),
            )

        elif session.current_state == StateType.FAILED:
            # Show error
            capabilities.append(
                Capability(
                    capability_type=CapabilityType.SHOW_ERROR,
                    data={},
                    message='Đã xảy ra lỗi, vui lòng thử lại',
                ),
            )

        return capabilities

    def should_require_confirmation(
        self,
        session: Session,
        validation_result: Any,
    ) -> bool:
        """
        Determine if confirmation is needed before execution.

        Confirmation is required for:
        - High-value transactions
        - Sensitive operations
        - Actions specified by plugin
        """

        # Check plugin preference
        plugin = get_intent_plugin(session.current_intent.value)
        if plugin:
            # TODO: Add plugin method to specify confirmation requirement
            pass

        # Business rules
        if session.current_intent == IntentType.SEND_MONEY:
            # Require confirmation for transfers > 1M VND
            amount = session.parameters.get('amount', 0)
            if amount > 1_000_000:
                return True

        return False
