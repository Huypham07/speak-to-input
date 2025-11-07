from __future__ import annotations

from typing import Any
from typing import Dict

from domain.entities import ExecutionResult
from domain.value_objects import IntentType

from .base_intent_plugin import IntentPlugin


class CheckBalancePlugin(IntentPlugin):
    """Plugin for CHECK_BALANCE intent"""

    # ========== Metadata ==========

    @property
    def intent_type(self) -> str:
        return IntentType.CHECK_BALANCE.value

    @property
    def display_name(self) -> str:
        return 'Kiểm tra số dư'

    @property
    def description(self) -> str:
        return 'Check account balance and available funds'

    @property
    def requires_voice_confirmation(self) -> bool:
        """Read-only operation, no confirmation needed"""
        return False

    # ========== Parameter Schema ==========

    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            'type': 'object',
            'properties': {
                'account_number': {
                    'type': 'string',
                    'description': 'Specific account to check (optional, defaults to primary account)',
                },
            },
        }

    # ========== Execution ==========

    async def execute(
        self,
        parameters: Dict[str, Any],
        context: Dict[str, Any],
    ) -> ExecutionResult:
        """Check account balance

        Optional parameters:
        - account_number: Specific account to check

        Required in context:
        - user_id: User requesting balance info
        - account_repository: AccountRepository instance
        """
        try:
            # Get dependencies
            account_repo = context.get('account_repository')
            user_id = context.get('user_id')

            if not all([account_repo, user_id]):
                return ExecutionResult(
                    success=False,
                    message='Missing required dependencies',
                    data={},
                )

            assert account_repo is not None
            assert user_id is not None

            # Get account
            account_number = parameters.get('account_number')

            if account_number:
                # Check specific account
                account = await account_repo.get_by_account_number(account_number)
                if not account:
                    return ExecutionResult(
                        success=False,
                        message=f'Không tìm thấy tài khoản {account_number}',
                        data={},
                    )
                if account.user_id != user_id:
                    return ExecutionResult(
                        success=False,
                        message='Bạn không có quyền truy cập tài khoản này',
                        data={},
                    )
            else:
                # Get primary account
                accounts = await account_repo.get_by_user_id(user_id)
                if not accounts:
                    return ExecutionResult(
                        success=False,
                        message='Không tìm thấy tài khoản',
                        data={},
                    )
                account = accounts[0]  # Use first account as primary

            # Format balance message
            balance_formatted = f'{account.balance:,.0f}'.replace(',', '.')

            return ExecutionResult(
                success=True,
                message=f'Số dư tài khoản {account.account_number}: {balance_formatted} VND',
                data={
                    'account_number': account.account_number,
                    'balance': float(account.balance),
                    'currency': 'VND',
                },
            )

        except Exception as e:
            return ExecutionResult(
                success=False,
                message=f'Lỗi khi kiểm tra số dư: {str(e)}',
                data={},
            )
