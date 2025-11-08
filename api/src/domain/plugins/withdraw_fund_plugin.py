from __future__ import annotations

from decimal import Decimal
from typing import Any
from typing import Dict

from domain.entities import ExecutionResult
from domain.entities import Transaction
from domain.value_objects import IntentType

from .base_intent_plugin import IntentPlugin


class WithdrawFundPlugin(IntentPlugin):
    """Plugin for WITHDRAW_FUND intent - Simplified for direct execution"""

    # ========== Metadata ==========

    @property
    def intent_type(self) -> str:
        return IntentType.WITHDRAW_FUND.value

    @property
    def display_name(self) -> str:
        return 'Rút tiền từ quỹ'

    @property
    def description(self) -> str:
        return 'Withdraw money from a savings fund'

    # ========== Parameter Schema ==========

    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            'type': 'object',
            'required': ['amount'],
            'properties': {
                'fund_id': {
                    'type': 'integer',
                    'description': 'Fund ID to withdraw from',
                    'minimum': 1,
                },
                'fund_name': {
                    'type': 'string',
                    'description': 'Fund name to withdraw from (alternative to fund_id)',
                },
                'amount': {
                    'type': 'number',
                    'minimum': 1000,
                    'maximum': 10000000000,
                    'description': 'Amount to withdraw in VND',
                },
                'to_account_id': {
                    'type': 'integer',
                    'description': 'Account ID to deposit to (optional, uses default if not provided)',
                    'minimum': 1,
                },
            },
        }

    # ========== Execution ==========

    async def execute(
        self,
        parameters: Dict[str, Any],
        context: Dict[str, Any],
    ) -> ExecutionResult:
        """Execute fund withdrawal with inline validation

        Required in context:
        - user_id: User performing the withdrawal
        - fund_repository: SavingsFundRepository instance
        - account_repository: AccountRepository instance
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
                    message='Vui lòng cung cấp ID hoặc tên quỹ cần rút tiền',
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

            amount = parameters.get('amount')
            if not amount:
                return ExecutionResult(
                    success=False,
                    message='Số tiền là bắt buộc',
                    data={},
                )
            if amount < 1000:
                return ExecutionResult(
                    success=False,
                    message='Số tiền phải từ 1,000 VND trở lên',
                    data={},
                )
            amount = Decimal(str(amount))

            to_account_id = parameters.get('to_account_id')

            # Check ownership
            if fund.user_id != int(user_id):
                return ExecutionResult(
                    success=False,
                    message='Bạn không có quyền rút tiền từ quỹ này',
                    data={},
                )

            # Check ownership
            if fund.user_id != int(user_id):
                return ExecutionResult(
                    success=False,
                    message='Không có quyền truy cập quỹ này',
                    data={},
                )

            # Check fund balance
            if fund.current_amount < amount:
                return ExecutionResult(
                    success=False,
                    message=f'Số tiền trong quỹ không đủ. Số tiền hiện có: {fund.current_amount:,.0f} VND',
                    data={},
                )

            # Get account
            if to_account_id:
                account = await account_repo.read_by_id(int(to_account_id))
                if not account:
                    return ExecutionResult(
                        success=False,
                        message='Tài khoản không tồn tại',
                        data={},
                    )
                if account.user_id != int(user_id):
                    return ExecutionResult(
                        success=False,
                        message='Không có quyền truy cập tài khoản này',
                        data={},
                    )
            else:
                # Use default account (first active account)
                user_accounts = await account_repo.get_by_user_id(int(user_id))
                if not user_accounts:
                    return ExecutionResult(
                        success=False,
                        message='Không tìm thấy tài khoản',
                        data={},
                    )
                account = user_accounts[0]

            # Withdraw from fund
            updated_fund = await fund_repo.withdraw(
                fund_id=fund_id,
                amount=amount,
            )

            # Add to account
            await account_repo.update_balance(
                account_id=account.id,
                amount=amount,
                operation='add',
            )

            # Create transaction record
            # From account perspective: money comes in (deposit to account)
            transaction = Transaction(
                user_id=int(user_id),
                from_account_id=None,  # Fund is not an account
                to_account_id=account.id,
                transaction_type='deposit',  # From account perspective: money deposited
                amount=amount,
                currency='VND',
                message=f'Rút tiền từ quỹ "{updated_fund.fund_name}"',
                status='completed',
                extra_data={
                    'fund_id': fund_id,
                    'fund_name': updated_fund.fund_name,
                    'transaction_category': 'fund_withdraw',
                },
            )
            await transaction_repo.create(transaction)

            # Calculate progress
            progress_percentage = (
                round(float(updated_fund.current_amount / updated_fund.target_amount * 100), 2)
                if updated_fund.target_amount > 0
                else 0
            )

            message = f'Đã rút {amount:,} VND từ quỹ "{updated_fund.fund_name}"'

            return ExecutionResult(
                success=True,
                message=message,
                data={
                    'fund_id': updated_fund.id,
                    'current_amount': float(updated_fund.current_amount),
                    'withdraw_amount': float(amount),
                    'progress_percentage': progress_percentage,
                    'status': updated_fund.status,
                },
            )

        except ValueError as e:
            return ExecutionResult(
                success=False,
                message=f'Lỗi: {str(e)}',
                data={},
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                message=f'Có lỗi xảy ra khi rút tiền từ quỹ: {str(e)}',
                data={},
            )
