from __future__ import annotations

from decimal import Decimal
from typing import Any
from typing import Dict

from domain.entities import ExecutionResult
from domain.entities import Transaction
from domain.value_objects import IntentType

from .base_intent_plugin import IntentPlugin


class DeleteFundPlugin(IntentPlugin):
    """Plugin for DELETE_FUND intent - Simplified for direct execution"""

    # ========== Metadata ==========

    @property
    def intent_type(self) -> str:
        return IntentType.DELETE_FUND.value

    @property
    def display_name(self) -> str:
        return 'Xóa quỹ tiết kiệm'

    @property
    def description(self) -> str:
        return 'Delete a savings fund'

    # ========== Parameter Schema ==========

    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            'type': 'object',
            'properties': {
                'fund_id': {
                    'type': 'integer',
                    'description': 'Fund ID to delete',
                    'minimum': 1,
                },
                'fund_name': {
                    'type': 'string',
                    'description': 'Fund name to delete (alternative to fund_id)',
                },
            },
        }

    # ========== Execution ==========

    async def execute(
        self,
        parameters: Dict[str, Any],
        context: Dict[str, Any],
    ) -> ExecutionResult:
        """Execute fund deletion with inline validation

        Required in context:
        - user_id: User performing the deletion
        - fund_repository: SavingsFundRepository instance
        """
        try:
            # Get repositories from context
            fund_repo = context.get('fund_repository')
            account_repo = context.get('account_repository')
            transaction_repo = context.get('transaction_repository')
            user_id = context.get('user_id')

            if not all([fund_repo, account_repo, transaction_repo, user_id]):
                return ExecutionResult(
                    success=False,
                    message='Missing required dependencies in context',
                    data={},
                )

            # Type assertions after null check
            assert fund_repo is not None
            assert transaction_repo is not None
            assert account_repo is not None
            assert user_id is not None

            # Validate and extract parameters
            fund_id = parameters.get('fund_id')
            fund_name = parameters.get('fund_name')

            if not fund_id and not fund_name:
                return ExecutionResult(
                    success=False,
                    message='Vui lòng cung cấp ID hoặc tên quỹ cần xóa',
                    data={},
                )

            # Find fund by ID or name
            fund = None

            if fund_id:
                fund = await fund_repo.read_by_id(int(fund_id))
            elif fund_name:
                # Get all user's funds and match by name
                user_funds = await fund_repo.get_by_user_id(user_id)
                matching_funds = [f for f in user_funds if f.fund_name.lower() == fund_name.lower()]

                if len(matching_funds) == 0:
                    return ExecutionResult(
                        success=False,
                        message=f'Không tìm thấy quỹ với tên "{fund_name}"',
                        data={},
                    )
                elif len(matching_funds) > 1:
                    return ExecutionResult(
                        success=False,
                        message=f'Tìm thấy nhiều quỹ trùng tên "{fund_name}". Vui lòng chỉ định rõ hơn hoặc dùng ID.',
                        data={'matching_count': len(matching_funds)},
                    )
                fund = matching_funds[0]

            if not fund:
                return ExecutionResult(
                    success=False,
                    message='Không tìm thấy quỹ tiết kiệm',
                    data={},
                )

            # Check ownership
            if fund.user_id != int(user_id):
                return ExecutionResult(
                    success=False,
                    message='Không có quyền truy cập quỹ này',
                    data={},
                )

            # If fund has balance, return it to main account
            refund_message = ''
            refunded_amount = 0.0
            if fund.current_amount > 0:
                # Save amount before withdrawing
                refunded_amount = float(fund.current_amount)

                # Get user's main account (first account)
                user_accounts = await account_repo.get_by_user_id(int(user_id))
                if not user_accounts:
                    return ExecutionResult(
                        success=False,
                        message='Không tìm thấy tài khoản để trả tiền',
                        data={},
                    )

                main_account = user_accounts[0]

                # Withdraw from fund (this will set current_amount to 0)
                await fund_repo.withdraw(
                    fund_id=fund_id,
                    amount=Decimal(str(refunded_amount)),
                )

                # Add to main account
                await account_repo.update_balance(
                    account_id=main_account.id,
                    amount=Decimal(str(refunded_amount)),
                    operation='add',
                )

                # Create transaction record for refund
                transaction = Transaction(
                    user_id=int(user_id),
                    from_account_id=None,  # Fund is not an account
                    to_account_id=main_account.id,
                    transaction_type='deposit',
                    amount=Decimal(str(refunded_amount)),
                    currency='VND',
                    message=f'Trả tiền từ quỹ "{fund.fund_name}" (đã xóa) về tài khoản chính',
                    status='completed',
                    extra_data={
                        'fund_id': fund_id,
                        'fund_name': fund.fund_name,
                        'transaction_category': 'fund_delete_refund',
                    },
                )
                await transaction_repo.create(transaction)

                refund_message = f'Tự động trả {refunded_amount:,.0f} VND về tài khoản chính.'

            # Delete fund
            await fund_repo.delete_by_id(fund_id)

            message = f'Đã xóa quỹ tiết kiệm "{fund.fund_name}" thành công.{refund_message}'

            return ExecutionResult(
                success=True,
                message=message,
                data={
                    'fund_id': fund_id,
                    'deleted': True,
                    'refunded_amount': refunded_amount,
                },
            )

        except Exception as e:
            return ExecutionResult(
                success=False,
                message=f'Có lỗi xảy ra khi xóa quỹ: {str(e)}',
                data={},
            )
