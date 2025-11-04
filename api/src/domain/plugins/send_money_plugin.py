from __future__ import annotations

from decimal import Decimal
from typing import Any
from typing import Dict
from typing import Optional

from domain.entities import ExecutionResult
from domain.entities import Transaction
from domain.value_objects import IntentType

from .base_intent_plugin import IntentPlugin


class SendMoneyPlugin(IntentPlugin):
    """Plugin for SEND_MONEY intent"""

    def __init__(self):
        super().__init__()

    # ========== Metadata ==========

    @property
    def intent_type(self) -> str:
        return IntentType.SEND_MONEY.value

    @property
    def display_name(self) -> str:
        return 'Chuyển tiền'

    @property
    def description(self) -> str:
        return 'Transfer money to another account or contact'

    # ========== Parameter Schema ==========

    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            'type': 'object',
            'required': ['amount', 'recipient'],
            'properties': {
                'amount': {
                    'type': 'number',
                    'minimum': 10000,
                    'maximum': 50000000,
                    'description': 'Transfer amount in VND',
                },
                'recipient': {
                    'type': 'string',
                    'description': 'Recipient identifier (contact ID or account number)',
                },
                'message': {
                    'type': 'string',
                    'maxLength': 200,
                    'description': 'Transfer message',
                },
            },
        }

    # ========== Execution ==========

    async def execute(
        self,
        parameters: Dict[str, Any],
        context: Dict[str, Any],
    ) -> ExecutionResult:
        """Execute money transfer

        Validates parameters and executes transfer immediately.
        Raises clear errors for missing or invalid fields.

        Required parameters:
        - amount: Transfer amount (must be between 10,000 and 50,000,000 VND)
        - recipient: Recipient account number or contact name

        Optional parameters:
        - message: Transfer message

        Required in context:
        - user_id: User performing the transfer
        - transaction_repository: TransactionRepository instance
        - account_repository: AccountRepository instance
        - contact_repository: ContactRepository instance
        """
        try:
            # Get repositories from context
            transaction_repo = context.get('transaction_repository')
            account_repo = context.get('account_repository')
            contact_repo = context.get('contact_repository')
            user_id = context.get('user_id')

            if not all([transaction_repo, account_repo, contact_repo, user_id]):
                return ExecutionResult(
                    success=False,
                    message='Missing required dependencies in context',
                    data={},
                )

            # Type assertions after null check
            assert transaction_repo is not None
            assert account_repo is not None
            assert contact_repo is not None
            assert user_id is not None

            # === VALIDATE REQUIRED FIELDS ===

            # Validate amount
            amount_value = parameters.get('amount')
            if amount_value is None:
                return ExecutionResult(
                    success=False,
                    message='Vui lòng nhập số tiền cần chuyển',
                    data={'field': 'amount', 'error_type': 'MISSING_FIELD'},
                )

            try:
                amount = Decimal(str(amount_value))
                if amount < 10000:
                    return ExecutionResult(
                        success=False,
                        message='Số tiền chuyển tối thiểu là 10,000 VND',
                        data={'field': 'amount', 'error_type': 'INVALID_VALUE', 'min': 10000},
                    )
                if amount > 50000000:
                    return ExecutionResult(
                        success=False,
                        message='Số tiền chuyển tối đa là 50,000,000 VND',
                        data={'field': 'amount', 'error_type': 'INVALID_VALUE', 'max': 50000000},
                    )
            except (ValueError, TypeError):
                return ExecutionResult(
                    success=False,
                    message='Số tiền không hợp lệ',
                    data={'field': 'amount', 'error_type': 'INVALID_FORMAT'},
                )

            # Validate recipient
            recipient = parameters.get('recipient', '').strip()
            if not recipient:
                return ExecutionResult(
                    success=False,
                    message='Vui lòng nhập số tài khoản người nhận',
                    data={'field': 'recipient', 'error_type': 'MISSING_FIELD'},
                )

            message = parameters.get('message', '')

            # === EXECUTE TRANSFER ===

            # Get user's account (assume first active account)
            user_accounts = await account_repo.get_by_user_id(int(user_id))
            if not user_accounts:
                return ExecutionResult(
                    success=False,
                    message='Không tìm thấy tài khoản của bạn',
                    data={},
                )

            from_account = user_accounts[0]

            # Check balance
            if Decimal(str(from_account.balance)) < amount:
                return ExecutionResult(
                    success=False,
                    message=f'Số dư không đủ. Số dư hiện tại: {from_account.balance:,} VND',
                    data={'balance': float(from_account.balance), 'error_type': 'INSUFFICIENT_BALANCE'},
                )

            # Resolve recipient
            recipient_info = await self._resolve_recipient(
                recipient=recipient,
                user_id=int(user_id),
                contact_repo=contact_repo,
                account_repo=account_repo,
            )

            if not recipient_info:
                return ExecutionResult(
                    success=False,
                    message=f'Không tìm thấy người nhận: {recipient}',
                    data={'field': 'recipient', 'error_type': 'NOT_FOUND'},
                )

            if recipient_info.get('account_id') == from_account.id:
                return ExecutionResult(
                    success=False,
                    message='Không thể chuyển tiền vào cùng một tài khoản',
                    data={'field': 'recipient', 'error_type': 'SAME_ACCOUNT'},
                )

            # Determine if internal or external transfer
            if recipient_info.get('account_id'):
                # Internal transfer (between accounts in system)
                to_account_id = recipient_info['account_id']

                # Perform transfer
                updated_from, updated_to = await account_repo.transfer(
                    from_account_id=int(from_account.id),
                    to_account_id=to_account_id,
                    amount=amount,
                )

                # Create transaction record for sender
                sender_transaction = Transaction(
                    user_id=int(user_id),
                    from_account_id=int(from_account.id),
                    to_account_id=to_account_id,
                    transaction_type='transfer',
                    amount=amount,
                    currency='VND',
                    message=message,
                    status='completed',
                )

                sender_txn = await transaction_repo.create(sender_transaction)
                await transaction_repo.update_status(sender_txn.id, 'completed')

                # Create transaction record for recipient (if different user)
                if updated_to.user_id != int(user_id):
                    recipient_transaction = Transaction(
                        user_id=updated_to.user_id,
                        from_account_id=int(from_account.id),
                        to_account_id=to_account_id,
                        transaction_type='transfer',
                        amount=amount,
                        currency='VND',
                        message=message,
                        status='completed',
                    )
                    recipient_txn = await transaction_repo.create(recipient_transaction)
                    await transaction_repo.update_status(recipient_txn.id, 'completed')

                return ExecutionResult(
                    success=True,
                    message=f'Chuyển {amount:,} VND thành công đến {recipient_info["name"]}',
                    data={
                        'transaction_id': sender_txn.id,
                        'amount': float(amount),
                        'recipient': recipient_info['name'],
                        'new_balance': float(updated_from.balance),
                    },
                )
            else:
                # External transfer (to external bank account)
                # Just deduct from account and create pending transaction
                updated_account = await account_repo.update_balance(
                    account_id=int(from_account.id),
                    amount=amount,
                    operation='subtract',
                )

                # Create transaction record
                transaction = Transaction(
                    user_id=int(user_id),
                    from_account_id=int(from_account.id),
                    to_account_id=None,
                    transaction_type='transfer',
                    amount=amount,
                    currency='VND',
                    recipient_account_number=recipient_info.get('account_number'),
                    recipient_name=recipient_info.get('name'),
                    recipient_bank=recipient_info.get('bank'),
                    message=message,
                    status='pending',
                )

                created_txn = await transaction_repo.create(transaction)

                # TODO: Call external banking API
                # For now, mark as completed
                await transaction_repo.update_status(created_txn.id, 'completed')

                return ExecutionResult(
                    success=True,
                    message=f'Chuyển {amount:,} VND thành công đến {recipient_info["name"]}',
                    data={
                        'transaction_id': created_txn.id,
                        'amount': float(amount),
                        'recipient': recipient_info['name'],
                        'recipient_account': recipient_info.get('account_number'),
                        'new_balance': float(updated_account.balance),
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
                message=f'Có lỗi xảy ra: {str(e)}',
                data={},
            )

    async def _resolve_recipient(
        self,
        recipient: str,
        user_id: int,
        contact_repo,
        account_repo,
    ) -> Optional[Dict[str, Any]]:
        """Resolve recipient from account number

        Returns:
        - For internal transfer: {'account_id': int, 'name': str}
        - For external transfer: {'account_number': str, 'name': str, 'bank': str}

        Note: Contact repository is kept for future voice-input feature
        where users can say contact names instead of account numbers.
        """
        # Try to find account by account number (internal transfer)
        account = await account_repo.get_by_account_number(recipient)
        if account:
            return {
                'account_id': int(account.id),
                'name': account.account_name,
            }

        # Not found in internal accounts - assume external transfer
        # For now, return None to indicate recipient not found
        # TODO: For voice input, search in contacts by name
        return None
