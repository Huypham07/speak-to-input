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
from domain.value_objects import CapabilityType
from domain.value_objects import FieldStatus

from .base_intent_plugin import IntentPlugin


class WithdrawFundPlugin(IntentPlugin):
    """Plugin for WITHDRAW_FUND intent - Rút tiền từ quỹ tiết kiệm"""

    # ========== Metadata ==========

    @property
    def intent_type(self) -> str:
        return 'WITHDRAW_FUND'

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
            'required': ['fund_id', 'amount'],
            'properties': {
                'fund_id': {
                    'type': 'integer',
                    'description': 'Fund ID to withdraw from',
                    'minimum': 1,
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

    # ========== Validation ==========

    def validate_parameters(
        self,
        parameters: Dict[str, Any],
        context: Dict[str, Any],
    ) -> ValidationResult:
        """Validate withdraw parameters (minimal validation - detailed validation in execute)"""
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
        """Resolve capabilities for fund withdrawal (for speech-to-input flow)"""
        capabilities = []

        # Request confirmation if validation passes (for speech-to-input)
        if validation_result.is_valid:
            capabilities.append(
                Capability(
                    capability_type=CapabilityType.REQUEST_CONFIRMATION,
                    data={
                        'message': f'Rút {parameters.get("amount", 0):,.0f} VND từ quỹ?',
                        'parameters': parameters,
                    },
                    message='Xác nhận rút tiền từ quỹ',
                ),
            )

        return capabilities

    # ========== Execution ==========

    async def execute(
        self,
        parameters: Dict[str, Any],
        context: Dict[str, Any],
    ) -> ExecutionResult:
        """Execute fund withdrawal

        Required in context:
        - user_id: User performing the withdrawal
        - fund_repository: SavingsFundRepository instance
        - account_repository: AccountRepository instance
        """
        try:
            # Get repositories from context
            fund_repo = context.get('fund_repository')
            account_repo = context.get('account_repository')
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
            to_account_id = parameters.get('to_account_id')

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
            error_msg = str(e)
            if 'Insufficient fund balance' in error_msg:
                return ExecutionResult(
                    success=False,
                    message=f'Số tiền trong quỹ không đủ. Số tiền hiện có: {fund.current_amount:,.0f} VND',
                    data={},
                )
            return ExecutionResult(
                success=False,
                message=f'Lỗi: {error_msg}',
                data={},
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                message=f'Có lỗi xảy ra khi rút tiền từ quỹ: {str(e)}',
                data={},
            )
