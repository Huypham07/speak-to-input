from __future__ import annotations

from decimal import Decimal
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from domain.entities import BusinessState
from domain.entities import Capability
from domain.entities import ExecutionResult
from domain.entities import FieldValidation
from domain.entities import Transaction
from domain.entities import ValidationResult
from domain.value_objects import CapabilityType
from domain.value_objects import FieldStatus

from .base_intent_plugin import IntentPlugin


class SendMoneyPlugin(IntentPlugin):
    """Plugin for SEND_MONEY intent"""

    def __init__(self):
        super().__init__()
        # Repositories will be injected via context
        self._transaction_repo = None
        self._account_repo = None
        self._contact_repo = None

    # ========== Metadata ==========

    @property
    def intent_type(self) -> str:
        return 'SEND_MONEY'

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

    # ========== Validation ==========

    def validate_parameters(
        self,
        parameters: Dict[str, Any],
        context: Dict[str, Any],
    ) -> ValidationResult:
        """Validate transfer parameters"""
        results = []

        # Validate amount
        amount = parameters.get('amount')
        if not amount:
            results.append(
                FieldValidation(
                    field_name='amount',
                    status=FieldStatus.MISSING,
                    confidence=0.0,
                ),
            )
        elif amount < 10000 or amount > 50000000:
            results.append(
                FieldValidation(
                    field_name='amount',
                    status=FieldStatus.INVALID,
                    value=amount,
                    confidence=0.0,
                    error_message='Số tiền phải từ 10,000 đến 50,000,000 VND',
                ),
            )
        else:
            # Check user balance (async check would be in orchestration service)
            results.append(
                FieldValidation(
                    field_name='amount',
                    status=FieldStatus.VALID,
                    value=amount,
                    confidence=1.0,
                ),
            )

        # Validate recipient
        recipient = parameters.get('recipient')
        if not recipient:
            results.append(
                FieldValidation(
                    field_name='recipient',
                    status=FieldStatus.MISSING,
                    confidence=0.0,
                ),
            )
        else:
            # Mark as valid - actual resolution happens in execute()
            # TODO: Could check for ambiguous contacts here
            results.append(
                FieldValidation(
                    field_name='recipient',
                    status=FieldStatus.VALID,
                    value=recipient,
                    confidence=1.0,
                ),
            )

        # Determine overall validity
        is_valid = all(r.status == FieldStatus.VALID for r in results)
        missing = [r for r in results if r.status == FieldStatus.MISSING]
        invalid = [r for r in results if r.status == FieldStatus.INVALID]
        ambiguous = [r for r in results if r.status == FieldStatus.AMBIGUOUS]

        return ValidationResult(
            is_valid=is_valid,
            field_results=results,
            missing_fields=missing,
            invalid_fields=invalid,
            ambiguous_fields=ambiguous,
        )

    # ========== Capability Resolution ==========

    def resolve_capabilities(
        self,
        parameters: Dict[str, Any],
        validation_result: ValidationResult,
        state: BusinessState,
    ) -> List[Capability]:
        """Resolve capabilities based on validation"""
        capabilities = []

        # If amount is missing, request it
        if validation_result.missing_fields:
            for field in validation_result.missing_fields:
                if field.field_name == 'amount':
                    capabilities.append(
                        Capability(
                            capability_type=CapabilityType.REQUEST_FIELD,
                            priority=1,
                            data={
                                'field': 'amount',
                                'message': 'Bạn muốn chuyển bao nhiêu?',
                            },
                        ),
                    )
                elif field.field_name == 'recipient':
                    capabilities.append(
                        Capability(
                            capability_type=CapabilityType.REQUEST_FIELD,
                            priority=2,
                            data={
                                'field': 'recipient',
                                'message': 'Chuyển cho ai?',
                            },
                        ),
                    )

        return capabilities

    # ========== State Machine ==========

    # ========== Execution ==========

    async def execute(
        self,
        parameters: Dict[str, Any],
        context: Dict[str, Any],
    ) -> ExecutionResult:
        """Execute money transfer

        Works for both:
        1. Speech-to-input: Called by OrchestrationService after user confirms
        2. Traditional API: Called directly from /transfers endpoint

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

            # Extract parameters
            amount = Decimal(str(parameters['amount']))
            recipient = parameters['recipient']
            message = parameters.get('message', '')

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
                    data={'balance': float(from_account.balance)},
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
                    data={},
                )

            # Determine if internal or external transfer
            if recipient_info.get('account_id'):
                # Internal transfer (between accounts in system)
                to_account_id = recipient_info['account_id']

                # Perform transfer
                updated_from, updated_to = await account_repo.transfer(
                    from_account_id=int(from_account.account_id),
                    to_account_id=to_account_id,
                    amount=amount,
                )

                # Create transaction record
                transaction = Transaction(
                    user_id=int(user_id),
                    from_account_id=int(from_account.account_id),
                    to_account_id=to_account_id,
                    transaction_type='transfer',
                    amount=amount,
                    currency='VND',
                    message=message,
                    status='completed',
                )

                created_txn = await transaction_repo.create(transaction)
                await transaction_repo.update_status(created_txn.transaction_id, 'completed')

                return ExecutionResult(
                    success=True,
                    message=f'Chuyển {amount:,} VND thành công đến {recipient_info["name"]}',
                    data={
                        'transaction_id': created_txn.transaction_id,
                        'amount': float(amount),
                        'recipient': recipient_info['name'],
                        'new_balance': float(updated_from.balance),
                    },
                )
            else:
                # External transfer (to external bank account)
                # Just deduct from account and create pending transaction
                updated_account = await account_repo.update_balance(
                    account_id=int(from_account.account_id),
                    amount=amount,
                    operation='subtract',
                )

                # Create transaction record
                transaction = Transaction(
                    user_id=int(user_id),
                    from_account_id=int(from_account.account_id),
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
                await transaction_repo.update_status(created_txn.transaction_id, 'completed')

                return ExecutionResult(
                    success=True,
                    message=f'Chuyển {amount:,} VND thành công đến {recipient_info["name"]}',
                    data={
                        'transaction_id': created_txn.transaction_id,
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
        """Resolve recipient from name/account number

        Returns:
        - For internal transfer: {'account_id': int, 'name': str}
        - For external transfer: {'account_number': str, 'name': str, 'bank': str}
        """
        # Try to find in contacts first (by name)
        contacts = await contact_repo.search_by_name(user_id, recipient)
        if contacts:
            contact = contacts[0]  # Take first match

            # Check if it's an internal account
            internal_account = await account_repo.get_by_account_number(contact.account_number)
            if internal_account:
                return {
                    'account_id': int(internal_account.account_id),
                    'name': contact.contact_name,
                }
            else:
                return {
                    'account_number': contact.account_number,
                    'name': contact.contact_name,
                    'bank': contact.bank_name,
                }

        # Try as account number
        account = await account_repo.get_by_account_number(recipient)
        if account:
            # Get account owner info
            return {
                'account_id': int(account.account_id),
                'name': account.account_name,
            }

        # Try to find in contacts by account number
        contact = await contact_repo.get_by_account_number(user_id, recipient)
        if contact:
            return {
                'account_number': contact.account_number,
                'name': contact.contact_name,
                'bank': contact.bank_name,
            }

        return None
