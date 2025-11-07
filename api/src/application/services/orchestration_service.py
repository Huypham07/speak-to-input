from __future__ import annotations

from typing import Any
from typing import Dict

from application.use_cases import execute_plugin
from domain.entities import ExecutionResult
from infra.db.repositories import AccountRepository
from infra.db.repositories import BillRepository
from infra.db.repositories import ContactRepository
from infra.db.repositories import SavingsFundRepository
from infra.db.repositories import TransactionRepository
from shared.logging import get_logger
from shared.settings import Settings

logger = get_logger(__name__)


class OrchestrationService:

    def __init__(
        self,
        settings: Settings,
        transaction_repository: TransactionRepository,
        account_repository: AccountRepository,
        contact_repository: ContactRepository,
        bill_repository: BillRepository,
        fund_repository: SavingsFundRepository,
    ):
        self.settings = settings
        self.transaction_repository = transaction_repository
        self.account_repository = account_repository
        self.contact_repository = contact_repository
        self.bill_repository = bill_repository
        self.fund_repository = fund_repository

    async def execute_intent(
        self,
        intent_type: str,
        parameters: Dict[str, Any],
        user_id: int,
    ) -> ExecutionResult:
        """
        Execute intent directly with parameters.

        Args:
            intent_type: Type of intent (SEND_MONEY, CREATE_BILL, etc.)
            parameters: Extracted parameters from Intent Service
            user_id: User ID

        Returns:
            ExecutionResult with success/failure and data
        """
        try:
            return await execute_plugin.execute(
                intent_type=intent_type,
                parameters=parameters,
                context={
                    'user_id': user_id,
                    'transaction_repository': self.transaction_repository,
                    'account_repository': self.account_repository,
                    'contact_repository': self.contact_repository,
                    'bill_repository': self.bill_repository,
                    'fund_repository': self.fund_repository,
                },
            )

        except ValueError as e:
            logger.error(f'Validation error for {intent_type}: {e}')
            return ExecutionResult(
                success=False,
                message=str(e),
                data={'error_type': 'VALIDATION_ERROR'},
            )
        except Exception as e:
            logger.error(f'Execution error for {intent_type}: {e}', exc_info=True)
            return ExecutionResult(
                success=False,
                message=f'Execution failed: {str(e)}',
                data={'error_type': 'EXECUTION_ERROR'},
            )
