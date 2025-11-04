from __future__ import annotations

from decimal import Decimal
from typing import Any
from typing import Dict
from typing import List

from domain.entities import BusinessState
from domain.entities import Capability
from domain.entities import ExecutionResult
from domain.entities import FieldValidation
from domain.entities import ValidationResult
from domain.entities.transaction import Transaction
from domain.value_objects import CapabilityType
from domain.value_objects import FieldStatus

from .base_intent_plugin import IntentPlugin


class DepositFundPlugin(IntentPlugin):
    """Plugin for DEPOSIT_FUND intent - Nạp tiền vào quỹ tiết kiệm"""

    # ========== Metadata ==========

    @property
    def intent_type(self) -> str:
        return 'DEPOSIT_FUND'

    @property
    def display_name(self) -> str:
        return 'Nạp tiền vào quỹ'

    @property
    def description(self) -> str:
        return 'Deposit money to a savings fund'

    # ========== Parameter Schema ==========

    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            'type': 'object',
            'required': ['fund_id', 'amount'],
            'properties': {
                'fund_id': {
                    'type': 'integer',
                    'description': 'Fund ID to deposit to',
                    'minimum': 1,
                },
                'amount': {
                    'type': 'number',
                    'minimum': 1000,
                    'maximum': 10000000000,
                    'description': 'Amount to deposit in VND',
                },
                'from_account_id': {
                    'type': 'integer',
                    'description': 'Account ID to withdraw from (optional, uses default if not provided)',
                    'minimum': 1,
                },
            },
        }

    # ========== Validation ==========

    def validate_parameters(
        self,
        parameters: Dict[str, Any],
        context: Dict[str, Any],
    ) -> ValidationResult:
        """Validate deposit parameters (minimal validation - detailed validation in execute)"""
        results = []

        for field in ['fund_id', 'amount']:
            if field not in parameters or parameters[field] is None:
                results.append(
                    FieldValidation(
                        field_name=field,
                        status=FieldStatus.MISSING,
                        confidence=0.0,
                    ),
                )
            else:
                results.append(
                    FieldValidation(
                        field_name=field,
                        status=FieldStatus.VALID,
                        value=parameters[field],
                        confidence=1.0,
                    ),
                )

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
        """Resolve capabilities for fund deposit (for speech-to-input flow)"""
        capabilities = []

        # Request confirmation if validation passes (for speech-to-input)
        if validation_result.is_valid:
            capabilities.append(
                Capability(
                    capability_type=CapabilityType.REQUEST_CONFIRMATION,
                    data={
                        'message': f'Nạp {parameters.get("amount", 0):,.0f} VND vào quỹ?',
                        'parameters': parameters,
                    },
                    message='Xác nhận nạp tiền vào quỹ',
                ),
            )

        return capabilities

    # ========== Execution ==========

    async def execute(
        self,
        parameters: Dict[str, Any],
        context: Dict[str, Any],
    ) -> ExecutionResult:
        """Execute fund deposit

        Required in context:
        - user_id: User performing the deposit
        - fund_repository: SavingsFundRepository instance
        - account_repository: AccountRepository instance
        - transaction_repository: TransactionRepository instance (optional, for transaction records)
        """
        try:
            # Get repositories from context
            fund_repo = context.get('fund_repository')
            account_repo = context.get('account_repository')
            transaction_repo = context.get('transaction_repository')
            user_id = context.get('user_id')

            if not fund_repo or not account_repo or not user_id:
                return ExecutionResult(
                    success=False,
                    message='Missing required dependencies in context',
                    data={},
                )

            # Extract parameters
            fund_id = int(parameters['fund_id'])
            amount = Decimal(str(parameters['amount']))
            from_account_id = parameters.get('from_account_id')

            # Get fund
            fund = await fund_repo.read_by_id(fund_id)
            if not fund:
                return ExecutionResult(
                    success=False,
                    message='Quỹ tiết kiệm không tồn tại',
                    data={},
                )

            # Check ownership
            if fund.user_id != int(user_id):
                return ExecutionResult(
                    success=False,
                    message='Không có quyền truy cập quỹ này',
                    data={},
                )

            # Get account
            if from_account_id:
                account = await account_repo.read_by_id(int(from_account_id))
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

            # Check account balance
            if Decimal(str(account.balance)) < amount:
                return ExecutionResult(
                    success=False,
                    message=f'Số dư không đủ. Số dư hiện tại: {account.balance:,} VND',
                    data={},
                )

            # Validate: không cho nạp nếu vượt quá target_amount
            new_total = fund.current_amount + amount
            if new_total > fund.target_amount:
                remaining = fund.target_amount - fund.current_amount
                return ExecutionResult(
                    success=False,
                    message=f'Không thể nạp vượt quá số tiền mục tiêu. Số tiền tối đa có thể nạp: {remaining:,.0f} VND',
                    data={},
                )

            # Deduct from account
            await account_repo.update_balance(
                account_id=account.id,
                amount=amount,
                operation='subtract',
            )

            # Deposit to fund
            updated_fund = await fund_repo.deposit(
                fund_id=fund_id,
                amount=amount,
            )

            # Create transaction record
            # From account perspective: money goes out (withdraw from account)
            if transaction_repo:
                transaction = Transaction(
                    user_id=int(user_id),
                    from_account_id=account.id,
                    to_account_id=None,  # Fund is not an account
                    transaction_type='withdraw',  # From account perspective: money withdrawn
                    amount=amount,
                    currency='VND',
                    message=f'Nạp tiền vào quỹ "{updated_fund.fund_name}"',
                    status='completed',
                    extra_data={
                        'fund_id': fund_id,
                        'fund_name': updated_fund.fund_name,
                        'transaction_category': 'fund_deposit',
                    },
                )
                await transaction_repo.create(transaction)

            # Calculate progress
            progress_percentage = (
                round(float(updated_fund.current_amount / updated_fund.target_amount * 100), 2)
                if updated_fund.target_amount > 0
                else 0
            )

            message = f'Đã nạp {amount:,} VND vào quỹ "{updated_fund.fund_name}"'

            return ExecutionResult(
                success=True,
                message=message,
                data={
                    'fund_id': updated_fund.id,
                    'current_amount': float(updated_fund.current_amount),
                    'deposit_amount': float(amount),
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
                message=f'Có lỗi xảy ra khi nạp tiền vào quỹ: {str(e)}',
                data={},
            )
