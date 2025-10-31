from __future__ import annotations

from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from application.services.intent_service import IntentUnderstandingInput
from application.services.intent_service import IntentUnderstandingService
from application.services.state_machine_service import StateMachineService
from domain.entities import Capability
from domain.entities.session import Session
from domain.plugins.registry import get_intent_plugin
from domain.value_objects import IntentType
from domain.value_objects import StateType
from infra.db.repositories.session_repository import SessionRepository
from pydantic import BaseModel
from pydantic import Field
from shared.logging import get_logger
from shared.settings import Settings

logger = get_logger(__name__)


class OrchestrationInput(BaseModel):
    """Input for orchestration"""

    session_id: str = Field(..., description='Session ID')
    user_id: Optional[str] = Field(None, description='User ID if authenticated')
    text: str = Field(..., description='User text input from ASR')

    # Context from previous interactions
    is_confirmation: bool = Field(
        default=False,
        description='Whether this is a confirmation response (yes/no)',
    )
    is_cancellation: bool = Field(
        default=False,
        description='Whether user wants to cancel',
    )


class OrchestrationOutput(BaseModel):
    """Output from orchestration"""

    session_id: str
    current_state: StateType

    # Intent information
    intent: Optional[IntentType] = None
    intent_confidence: float = 0.0

    # Capabilities for frontend
    capabilities: List[Capability] = Field(default_factory=list)

    # Response message
    message: str = ''

    # Current parameters
    parameters: Dict[str, Any] = Field(default_factory=dict)

    # Metadata
    requires_confirmation: bool = False
    turn_count: int = 0


class OrchestrationService:
    """
    Main orchestration service that coordinates:
    1. Session management
    2. Intent understanding
    3. State machine transitions
    4. Plugin execution
    """

    def __init__(
        self,
        settings: Settings,
        session_repository: SessionRepository,
        intent_service: IntentUnderstandingService,
        state_machine_service: StateMachineService,
        # Repositories for plugin execution
        transaction_repository=None,
        account_repository=None,
        contact_repository=None,
        bill_repository=None,
        fund_repository=None,
    ):
        self.settings = settings
        self.session_repository = session_repository
        self.intent_service = intent_service
        self.state_machine_service = state_machine_service

        # Store repositories for plugin context
        self.transaction_repository = transaction_repository
        self.account_repository = account_repository
        self.contact_repository = contact_repository
        self.bill_repository = bill_repository
        self.fund_repository = fund_repository

    async def process(self, input: OrchestrationInput) -> OrchestrationOutput:
        """
        Main orchestration flow:
        1. Load/create session
        2. Handle special commands (cancel, confirm, etc.)
        3. Process based on current state
        4. Update session
        5. Generate response
        """

        # 1. Load or create session
        session = await self.session_repository.get_or_create(
            session_id=input.session_id,
            user_id=input.user_id,
        )

        session.increment_turn()

        logger.info(
            f'Processing session {session.session_id} '
            f'state={session.current_state} '
            f'intent={session.current_intent} '
            f'turn={session.turn_count}',
        )

        # 2. Handle special commands
        if input.is_cancellation:
            return await self._handle_cancellation(session)

        if input.is_confirmation and session.current_state == StateType.AWAITING_CONFIRMATION:
            return await self._handle_confirmation(session, confirmed=True)

        # 3. Process based on current state
        if session.current_state == StateType.IDLE:
            # New intent - classify
            output = await self._process_new_intent(session, input.text)

        elif session.current_state == StateType.INTENT_CLASSIFIED:
            # Validate parameters
            output = await self._process_validation(session)

        elif session.current_state == StateType.CLARIFYING:
            # User provided more info - extract and re-validate
            output = await self._process_clarification(session, input.text)

        elif session.current_state == StateType.DISAMBIGUATING:
            # User selected an option
            output = await self._process_disambiguation(session, input.text)

        elif session.current_state == StateType.AWAITING_CONFIRMATION:
            # Waiting for yes/no
            output = await self._process_confirmation_wait(session, input.text)

        elif session.current_state == StateType.EXECUTING:
            # Execute the intent
            output = await self._process_execution(session)

        elif session.current_state in [StateType.COMPLETED, StateType.FAILED]:
            # Reset and start new
            output = await self._process_new_intent(session, input.text)

        else:
            # Unknown state - reset
            session.reset()
            output = await self._process_new_intent(session, input.text)

        # 4. Save session
        await self.session_repository.save(session)

        return output

    async def _process_new_intent(
        self,
        session: Session,
        text: str,
    ) -> OrchestrationOutput:
        """Process new intent from IDLE state"""

        # Reset session for new intent
        session.reset()

        # Classify intent
        intent_result = await self.intent_service.process(
            IntentUnderstandingInput(
                text=text,
                context=session.context,
            ),
        )

        # Update session
        session.update_intent(
            intent=intent_result.intent_type,
            confidence=intent_result.confidence,
        )
        session.update_parameters(intent_result.parameters)

        # Transition state
        next_state = self.state_machine_service.get_next_state(
            current_state=StateType.IDLE,
            session=session,
        )
        session.update_state(next_state)

        if next_state == StateType.FAILED:
            return OrchestrationOutput(
                session_id=session.session_id,
                current_state=next_state,
                message='Xin lỗi, tôi không hiểu yêu cầu của bạn',
                turn_count=session.turn_count,
            )

        # Move to validation
        return await self._process_validation(session)

    async def _process_validation(self, session: Session) -> OrchestrationOutput:
        """Validate current parameters"""

        # Get plugin
        plugin = get_intent_plugin(session.current_intent.value)
        if not plugin:
            session.update_state(StateType.FAILED)
            return OrchestrationOutput(
                session_id=session.session_id,
                current_state=StateType.FAILED,
                message='Không tìm thấy xử lý cho yêu cầu này',
                turn_count=session.turn_count,
            )

        # Validate
        validation_result = plugin.validate_parameters(
            parameters=session.parameters,
            context=session.context,
        )

        # Check if confirmation is needed
        if validation_result.is_valid:
            requires_confirmation = self.state_machine_service.should_require_confirmation(
                session=session,
                validation_result=validation_result,
            )
            session.requires_confirmation = requires_confirmation

        # Determine next state
        next_state = self.state_machine_service.get_next_state(
            current_state=StateType.VALIDATING,
            session=session,
            validation_result=validation_result,
        )
        session.update_state(next_state)

        # Generate capabilities
        capabilities = self.state_machine_service.generate_capabilities(
            session=session,
            validation_result=validation_result,
        )

        # Generate message
        message = self._generate_message(session, validation_result)

        return OrchestrationOutput(
            session_id=session.session_id,
            current_state=next_state,
            intent=session.current_intent,
            intent_confidence=session.intent_confidence,
            capabilities=capabilities,
            message=message,
            parameters=session.parameters,
            requires_confirmation=session.requires_confirmation,
            turn_count=session.turn_count,
        )

    async def _process_clarification(
        self,
        session: Session,
        text: str,
    ) -> OrchestrationOutput:
        """Process user's clarification response"""

        # Get plugin
        plugin = get_intent_plugin(session.current_intent.value)
        if not plugin:
            session.update_state(StateType.FAILED)
            return OrchestrationOutput(
                session_id=session.session_id,
                current_state=StateType.FAILED,
                message='Đã xảy ra lỗi',
                turn_count=session.turn_count,
            )

        # Re-validate to get missing fields
        validation_result = plugin.validate_parameters(
            parameters=session.parameters,
            context=session.context,
        )

        # Extract missing data from user's response
        missing_field_names = [f.field_name for f in validation_result.missing_fields]

        extracted_data = await self.intent_service.extract_clarification_data(
            text=text,
            missing_fields=missing_field_names,
            current_data=session.parameters,
        )

        # Update parameters
        session.update_parameters(extracted_data)

        # Re-validate with new data
        return await self._process_validation(session)

    async def _process_disambiguation(
        self,
        session: Session,
        text: str,
    ) -> OrchestrationOutput:
        """Process user's disambiguation choice"""

        # TODO: Parse user's selection
        # For now, just re-validate
        return await self._process_validation(session)

    async def _process_confirmation_wait(
        self,
        session: Session,
        text: str,
    ) -> OrchestrationOutput:
        """Process user's response while waiting for confirmation"""

        # Parse yes/no
        text_lower = text.lower().strip()
        confirmed = any(word in text_lower for word in ['có', 'yes', 'đồng ý', 'ok', 'được'])
        rejected = any(word in text_lower for word in ['không', 'no', 'hủy', 'cancel'])

        if confirmed:
            return await self._handle_confirmation(session, confirmed=True)
        elif rejected:
            return await self._handle_cancellation(session)
        else:
            # Unclear response
            return OrchestrationOutput(
                session_id=session.session_id,
                current_state=session.current_state,
                intent=session.current_intent,
                capabilities=[],
                message='Vui lòng xác nhận "Có" hoặc "Không"',
                parameters=session.parameters,
                requires_confirmation=True,
                turn_count=session.turn_count,
            )

    async def _handle_confirmation(
        self,
        session: Session,
        confirmed: bool,
    ) -> OrchestrationOutput:
        """Handle user confirmation"""

        if confirmed:
            # Proceed to execution
            session.update_state(StateType.EXECUTING)
            return await self._process_execution(session)
        else:
            # Cancel
            return await self._handle_cancellation(session)

    async def _handle_cancellation(self, session: Session) -> OrchestrationOutput:
        """Handle user cancellation"""

        session.reset()
        session.update_state(StateType.IDLE)

        return OrchestrationOutput(
            session_id=session.session_id,
            current_state=StateType.IDLE,
            message='Đã hủy yêu cầu',
            turn_count=session.turn_count,
        )

    async def _process_execution(self, session: Session) -> OrchestrationOutput:
        """Execute the intent"""

        # Get plugin
        plugin = get_intent_plugin(session.current_intent.value)
        if not plugin:
            session.update_state(StateType.FAILED)
            return OrchestrationOutput(
                session_id=session.session_id,
                current_state=StateType.FAILED,
                message='Không thể thực hiện yêu cầu',
                turn_count=session.turn_count,
            )

        # Build context with repositories for plugin execution
        execution_context = {
            **session.context,
            'user_id': session.user_id,
            'session_id': session.session_id,
            # Inject repositories
            'transaction_repository': self.transaction_repository,
            'account_repository': self.account_repository,
            'contact_repository': self.contact_repository,
            'bill_repository': self.bill_repository,
            'fund_repository': self.fund_repository,
        }

        # Execute
        try:
            execution_result = await plugin.execute(
                parameters=session.parameters,
                context=execution_context,
            )

            if execution_result.success:
                session.update_state(StateType.COMPLETED)
                session.update_context(execution_result.data)

                capabilities = [
                    Capability(
                        capability_type='SHOW_SUCCESS',
                        message=execution_result.message,
                        data=execution_result.data,
                    ),
                ]

                return OrchestrationOutput(
                    session_id=session.session_id,
                    current_state=StateType.COMPLETED,
                    intent=session.current_intent,
                    capabilities=capabilities,
                    message=execution_result.message,
                    parameters=session.parameters,
                    turn_count=session.turn_count,
                )
            else:
                session.update_state(StateType.FAILED)
                return OrchestrationOutput(
                    session_id=session.session_id,
                    current_state=StateType.FAILED,
                    message=execution_result.message,
                    turn_count=session.turn_count,
                )

        except Exception as e:
            logger.error(f'Execution error: {e}', exc_info=True)
            session.update_state(StateType.FAILED)
            return OrchestrationOutput(
                session_id=session.session_id,
                current_state=StateType.FAILED,
                message='Đã xảy ra lỗi khi thực hiện',
                turn_count=session.turn_count,
            )

    def _generate_message(
        self,
        session: Session,
        validation_result: Any,
    ) -> str:
        """Generate user-friendly message based on state"""

        if session.current_state == StateType.CLARIFYING:
            if validation_result.missing_fields:
                field_names = [f.field_name for f in validation_result.missing_fields]
                return f'Vui lòng cung cấp: {", ".join(field_names)}'
            elif validation_result.invalid_fields:
                errors = [f.error_message for f in validation_result.invalid_fields if f.error_message]
                return errors[0] if errors else 'Thông tin không hợp lệ'

        elif session.current_state == StateType.DISAMBIGUATING:
            return 'Vui lòng chọn một trong các lựa chọn sau'

        elif session.current_state == StateType.AWAITING_CONFIRMATION:
            return 'Vui lòng xác nhận thông tin'

        elif session.current_state == StateType.EXECUTING:
            return 'Đang thực hiện...'

        return ''
