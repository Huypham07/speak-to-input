from __future__ import annotations

from decimal import Decimal
from typing import Annotated
from typing import Any
from typing import Dict
from typing import Optional

from domain.entities import ExecutionResult
from domain.entities import Transaction
from domain.value_objects import IntentType
from pydantic import BaseModel
from pydantic import Field

from .base_intent_plugin import IntentPlugin


class PayBillValidation(BaseModel):
    bill_id: Annotated[
        int,
        Field(description='Bill ID to pay', ge=1),
    ]

    from_account_id: Optional[
        Annotated[int, Field(description='Account to pay from (optional)', ge=1)]
    ] = None


class PayBillPlugin(IntentPlugin):
    """Plugin for PAY_BILL intent - Mark bill as paid and create transaction"""

    @property
    def intent_type(self) -> str:
        return IntentType.PAY_BILL.value

    @property
    def display_name(self) -> str:
        return 'Thanh toán hóa đơn'

    @property
    def description(self) -> str:
        return 'Pay a bill and record transaction'

    # ========== Parameter Schema ==========

    def get_parameter_schema(self) -> Dict[str, Any]:
        """Return parameter schema for PAY_BILL intent"""
        return {
            'type': 'object',
            'properties': {
                'bill_id': {
                    'type': 'integer',
                    'description': 'Bill ID to pay',
                    'minimum': 1,
                },
                'bill_name': {
                    'type': 'string',
                    'description': 'Bill name to pay (alternative to bill_id)',
                },
                'from_account_id': {
                    'type': 'integer',
                    'description': 'Account to pay from (optional)',
                    'minimum': 1,
                },
            },
        }

    # ========== Execute ==========

    async def execute(
        self,
        parameters: Dict[str, Any],
        context: Dict[str, Any],
    ) -> ExecutionResult:
        """
        Execute PAY_BILL intent:
        1. Validate bill exists and belongs to user
        2. Check if already paid
        3. Get user's account (or use specified account)
        4. Check sufficient balance
        5. Create transaction (debit from account)
        6. Mark bill as paid
        7. Return success with transaction details
        """

        # ========== Validate Parameters ==========
        bill_id = parameters.get('bill_id')
        bill_name = parameters.get('bill_name')
        from_account_id = parameters.get('from_account_id')

        if not bill_id and not bill_name:
            return ExecutionResult(
                success=False,
                message='Vui lòng cung cấp ID hoặc tên hóa đơn cần thanh toán',
                data={},
            )

        # ========== Get Dependencies ==========
        user_id = context.get('user_id')
        bill_repo = context.get('bill_repository')
        account_repo = context.get('account_repository')
        transaction_repo = context.get('transaction_repository')

        if not all([user_id, bill_repo, account_repo, transaction_repo]):
            return ExecutionResult(
                success=False,
                message='Missing required context (user_id, repositories)',
                data={},
            )

        # Type assertions after null check
        assert bill_repo is not None
        assert transaction_repo is not None
        assert account_repo is not None
        assert user_id is not None

        # ========== Find Bill by ID or Name ==========
        bill = None

        if bill_id:
            # Find by ID
            bill = await bill_repo.read_by_id(bill_id)
        elif bill_name:
            # Find by name (get all user's bills and match by name)
            user_bills = await bill_repo.get_by_user_id(user_id)
            matching_bills = [b for b in user_bills if b.bill_name.lower() == bill_name.lower()]

            if len(matching_bills) == 0:
                return ExecutionResult(
                    success=False,
                    message=f'Không tìm thấy hóa đơn với tên "{bill_name}"',
                    data={},
                )
            elif len(matching_bills) > 1:
                return ExecutionResult(
                    success=False,
                    message=f'Tìm thấy nhiều hóa đơn trùng tên "{bill_name}". Vui lòng chỉ định rõ hơn hoặc dùng ID.',
                    data={'matching_count': len(matching_bills)},
                )
            bill = matching_bills[0]

        if not bill:
            return ExecutionResult(
                success=False,
                message='Không tìm thấy hóa đơn',
                data={},
            )

        # Check ownership
        if bill.user_id != user_id:
            return ExecutionResult(
                success=False,
                message='Bạn không có quyền thanh toán hóa đơn này',
                data={},
            )

        # Check if already paid
        if bill.status == 'paid':
            return ExecutionResult(
                success=False,
                message=f'Hóa đơn "{bill.bill_name}" đã được thanh toán',
                data={
                    'bill_id': bill.id,
                    'bill_name': bill.bill_name,
                    'status': bill.status,
                    'paid_at': bill.paid_at.isoformat() if bill.paid_at else None,
                },
            )

        # ========== Get Account to Pay From ==========
        if from_account_id:
            # Use specified account
            account = await account_repo.read_by_id(from_account_id)
            if not account or account.user_id != user_id:
                return ExecutionResult(
                    success=False,
                    message=f'Không tìm thấy tài khoản ID {from_account_id}',
                    data={},
                )
        else:
            # Get user's primary account (first account)
            accounts = await account_repo.get_by_user_id(user_id)
            if not accounts:
                return ExecutionResult(
                    success=False,
                    message='Không tìm thấy tài khoản để thanh toán',
                    data={},
                )
            account = accounts[0]

        # ========== Check Balance ==========
        bill_amount = Decimal(str(bill.amount))
        account_balance = Decimal(str(account.balance))

        if account_balance < bill_amount:
            return ExecutionResult(
                success=False,
                message=f'Số dư không đủ. Cần {bill_amount:,.0f} VND, hiện có {account_balance:,.0f} VND',
                data={
                    'bill_amount': float(bill_amount),
                    'account_balance': float(account_balance),
                    'shortfall': float(bill_amount - account_balance),
                },
            )

        # ========== Create Transaction ==========
        try:
            # Mark bill as paid
            paid_bill = await bill_repo.mark_as_paid(bill_id)

            # Update account balance (deduct amount)
            await account_repo.update_balance(
                account_id=account.id,
                amount=bill_amount,
                operation='subtract',
            )

            transaction_entity = Transaction(
                user_id=user_id,
                from_account_id=account.id,
                to_account_id=None,
                transaction_type='withdraw',
                amount=bill_amount,
                currency='VND',
                message=f'Thanh toán hóa đơn: {bill.bill_name}',
                status='completed',
            )

            # Save transaction
            await transaction_repo.create(transaction_entity)

            return ExecutionResult(
                success=True,
                message=f'Đã thanh toán hóa đơn "{bill.bill_name}" thành công',
                data={
                    'bill_id': paid_bill.id,
                    'bill_name': paid_bill.bill_name,
                    'amount': paid_bill.amount,
                    'status': paid_bill.status,
                    'paid_at': paid_bill.paid_at.isoformat() if paid_bill.paid_at else None,
                },
            )

        except Exception as e:
            return ExecutionResult(
                success=False,
                message=f'Lỗi khi thanh toán hóa đơn: {str(e)}',
                data={},
            )
