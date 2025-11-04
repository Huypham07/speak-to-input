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


class DeleteFundPlugin(IntentPlugin):
    """Plugin for DELETE_FUND intent - Xóa quỹ tiết kiệm"""

    # ========== Metadata ==========

    @property
    def intent_type(self) -> str:
        return 'DELETE_FUND'

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
            'required': ['fund_id'],
            'properties': {
                'fund_id': {
                    'type': 'integer',
                    'description': 'Fund ID to delete',
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
        """Validate delete parameters (minimal validation - detailed validation in execute)"""
        results = []

        fund_id = parameters.get('fund_id')
        if not fund_id:
            results.append(
                FieldValidation(
                    field_name='fund_id',
                    status=FieldStatus.MISSING,
                    confidence=0.0,
                ),
            )
        else:
            results.append(
                FieldValidation(
                    field_name='fund_id',
                    status=FieldStatus.VALID,
                    value=fund_id,
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
        """Resolve capabilities for fund deletion (for speech-to-input flow)"""
        capabilities = []

        # Request confirmation if validation passes (for speech-to-input)
        if validation_result.is_valid:
            capabilities.append(
                Capability(
                    capability_type=CapabilityType.REQUEST_CONFIRMATION,
                    data={
                        'message': 'Bạn có chắc muốn xóa quỹ này?',
                        'parameters': parameters,
                        'warning': 'Hành động này không thể hoàn tác',
                    },
                    message='Xác nhận xóa quỹ tiết kiệm',
                ),
            )

        return capabilities

    # ========== Execution ==========

    async def execute(
        self,
        parameters: Dict[str, Any],
        context: Dict[str, Any],
    ) -> ExecutionResult:
        """Execute fund deletion

        Required in context:
        - user_id: User performing the deletion
        - fund_repository: SavingsFundRepository instance
        - account_repository: AccountRepository instance (required to return balance to main account)
        - transaction_repository: TransactionRepository instance (optional, for transaction records)
        """
        try:
            fund_repo = context.get('fund_repository')
            account_repo = context.get('account_repository')
            transaction_repo = context.get('transaction_repository')
            user_id = context.get('user_id')

            if not fund_repo or not user_id or not account_repo:
                return ExecutionResult(
                    success=False,
                    message='Missing required dependencies in context',
                    data={},
                )

            # Extract parameters
            fund_id = int(parameters['fund_id'])

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
                if transaction_repo:
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
