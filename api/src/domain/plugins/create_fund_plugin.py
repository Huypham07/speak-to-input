from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from typing import Dict
from typing import List

from domain.entities import BusinessState
from domain.entities import Capability
from domain.entities import ExecutionResult
from domain.entities import FieldValidation
from domain.entities import SavingsFund
from domain.entities import ValidationResult
from domain.value_objects import CapabilityType
from domain.value_objects import FieldStatus

from .base_intent_plugin import IntentPlugin


class CreateFundPlugin(IntentPlugin):
    """Plugin for CREATE_FUND intent - Tạo quỹ tiết kiệm"""

    # ========== Metadata ==========

    @property
    def intent_type(self) -> str:
        return 'CREATE_FUND'

    @property
    def display_name(self) -> str:
        return 'Tạo quỹ tiết kiệm'

    @property
    def description(self) -> str:
        return 'Create a savings fund/goal'

    # ========== Parameter Schema ==========

    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            'type': 'object',
            'required': ['fund_name', 'target_amount', 'target_date'],
            'properties': {
                'fund_name': {
                    'type': 'string',
                    'description': 'Fund/goal name (e.g., "Mua xe", "Du lịch")',
                    'minLength': 1,
                    'maxLength': 100,
                },
                'target_amount': {
                    'type': 'number',
                    'minimum': 100000,
                    'maximum': 10000000000,
                    'description': 'Target amount in VND',
                },
                'target_date': {
                    'type': 'string',
                    'format': 'date',
                    'description': 'Target date to reach goal (YYYY-MM-DD)',
                },
                'initial_amount': {
                    'type': 'number',
                    'minimum': 0,
                    'description': 'Initial deposit amount',
                    'default': 0,
                },
                'monthly_contribution': {
                    'type': 'number',
                    'minimum': 0,
                    'description': 'Planned monthly contribution',
                    'default': 0,
                },
                'category': {
                    'type': 'string',
                    'enum': ['travel', 'education', 'emergency', 'purchase', 'retirement', 'other'],
                    'description': 'Fund category',
                },
                'auto_transfer': {
                    'type': 'boolean',
                    'description': 'Enable automatic monthly transfer',
                    'default': False,
                },
                'notes': {
                    'type': 'string',
                    'maxLength': 500,
                    'description': 'Additional notes',
                },
            },
        }

    # ========== Validation ==========

    def validate_parameters(
        self,
        parameters: Dict[str, Any],
        context: Dict[str, Any],
    ) -> ValidationResult:
        """Validate fund parameters"""
        results = []

        # Validate fund_name
        fund_name = parameters.get('fund_name')
        if not fund_name:
            results.append(
                FieldValidation(
                    field_name='fund_name',
                    status=FieldStatus.MISSING,
                    confidence=0.0,
                ),
            )
        elif len(fund_name.strip()) < 1:
            results.append(
                FieldValidation(
                    field_name='fund_name',
                    status=FieldStatus.INVALID,
                    value=fund_name,
                    confidence=0.0,
                    error_message='Tên quỹ không được để trống',
                ),
            )
        else:
            results.append(
                FieldValidation(
                    field_name='fund_name',
                    status=FieldStatus.VALID,
                    value=fund_name,
                    confidence=1.0,
                ),
            )

        # Validate target_amount
        target_amount = parameters.get('target_amount')
        if not target_amount:
            results.append(
                FieldValidation(
                    field_name='target_amount',
                    status=FieldStatus.MISSING,
                    confidence=0.0,
                ),
            )
        elif target_amount < 100000:
            results.append(
                FieldValidation(
                    field_name='target_amount',
                    status=FieldStatus.INVALID,
                    value=target_amount,
                    confidence=0.0,
                    error_message='Số tiền mục tiêu phải từ 100,000 VND trở lên',
                ),
            )
        else:
            results.append(
                FieldValidation(
                    field_name='target_amount',
                    status=FieldStatus.VALID,
                    value=target_amount,
                    confidence=1.0,
                ),
            )

        # Validate target_date
        target_date = parameters.get('target_date')
        if not target_date:
            results.append(
                FieldValidation(
                    field_name='target_date',
                    status=FieldStatus.MISSING,
                    confidence=0.0,
                ),
            )
        else:
            # TODO: Validate date format and ensure it's in the future
            results.append(
                FieldValidation(
                    field_name='target_date',
                    status=FieldStatus.VALID,
                    value=target_date,
                    confidence=1.0,
                ),
            )

        # Validate initial_amount (optional)
        initial_amount = parameters.get('initial_amount', 0)
        if initial_amount < 0:
            results.append(
                FieldValidation(
                    field_name='initial_amount',
                    status=FieldStatus.INVALID,
                    value=initial_amount,
                    confidence=0.0,
                    error_message='Số tiền ban đầu không thể âm',
                ),
            )
        else:
            # TODO: Check user balance
            results.append(
                FieldValidation(
                    field_name='initial_amount',
                    status=FieldStatus.VALID,
                    value=initial_amount,
                    confidence=1.0,
                ),
            )

        # Validate monthly_contribution (optional but recommended)
        monthly_contribution = parameters.get('monthly_contribution')
        if monthly_contribution is None or monthly_contribution == 0:
            # Calculate suggested monthly contribution
            if target_amount and target_date:
                suggested = self._calculate_monthly_contribution(
                    target_amount,
                    target_date,
                    initial_amount,
                )
                results.append(
                    FieldValidation(
                        field_name='monthly_contribution',
                        status=FieldStatus.AMBIGUOUS,
                        value=suggested,
                        confidence=0.8,
                        metadata={
                            'suggested': suggested,
                            'message': f'Gợi ý đóng góp hàng tháng: {suggested:,.0f} VND',
                        },
                    ),
                )
        elif monthly_contribution < 0:
            results.append(
                FieldValidation(
                    field_name='monthly_contribution',
                    status=FieldStatus.INVALID,
                    value=monthly_contribution,
                    confidence=0.0,
                    error_message='Số tiền đóng góp hàng tháng không thể âm',
                ),
            )
        else:
            results.append(
                FieldValidation(
                    field_name='monthly_contribution',
                    status=FieldStatus.VALID,
                    value=monthly_contribution,
                    confidence=1.0,
                ),
            )

        # Validate category (optional, suggest if missing)
        category = parameters.get('category')
        if not category and fund_name:
            suggested_category = self._suggest_category(fund_name)
            if suggested_category:
                results.append(
                    FieldValidation(
                        field_name='category',
                        status=FieldStatus.AMBIGUOUS,
                        value=suggested_category,
                        confidence=0.7,
                        metadata={
                            'options': [
                                {'value': 'travel', 'label': 'Du lịch'},
                                {'value': 'education', 'label': 'Giáo dục'},
                                {'value': 'emergency', 'label': 'Khẩn cấp'},
                                {'value': 'purchase', 'label': 'Mua sắm'},
                                {'value': 'retirement', 'label': 'Hưu trí'},
                                {'value': 'other', 'label': 'Khác'},
                            ],
                            'suggested': suggested_category,
                        },
                    ),
                )
        else:
            results.append(
                FieldValidation(
                    field_name='category',
                    status=FieldStatus.VALID,
                    value=category,
                    confidence=1.0,
                ),
            )

        # Determine overall validity (category and monthly_contribution are optional)
        required_fields = ['fund_name', 'target_amount', 'target_date', 'initial_amount']
        is_valid = all(
            r.status == FieldStatus.VALID
            for r in results
            if r.field_name in required_fields
        )

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

    def _calculate_monthly_contribution(
        self,
        target_amount: float,
        target_date: str,
        initial_amount: float = 0,
    ) -> float:
        """Calculate suggested monthly contribution"""
        # TODO: Calculate based on target_date
        # For now, assume 12 months
        months = 12
        remaining = target_amount - initial_amount
        return max(0, remaining / months)

    def _suggest_category(self, fund_name: str) -> str:
        """Suggest category based on fund name"""
        if not fund_name:
            return 'other'

        name_lower = fund_name.lower()

        if any(word in name_lower for word in ['du lịch', 'travel', 'vacation', 'nghỉ']):
            return 'travel'
        elif any(word in name_lower for word in ['học', 'education', 'đại học', 'trường']):
            return 'education'
        elif any(word in name_lower for word in ['khẩn cấp', 'emergency', 'dự phòng']):
            return 'emergency'
        elif any(word in name_lower for word in ['mua', 'purchase', 'xe', 'nhà', 'máy']):
            return 'purchase'
        elif any(word in name_lower for word in ['hưu', 'retirement', 'về già']):
            return 'retirement'
        else:
            return 'other'

    # ========== Capability Resolution ==========

    def resolve_capabilities(
        self,
        parameters: Dict[str, Any],
        validation_result: ValidationResult,
        state: BusinessState,
    ) -> List[Capability]:
        """Resolve capabilities for fund creation"""
        capabilities = []

        # If all required fields are valid, show preview with calculations
        if validation_result.is_valid:
            target_amount = parameters.get('target_amount', 0)
            initial_amount = parameters.get('initial_amount', 0)
            monthly_contribution = parameters.get('monthly_contribution', 0)

            # Calculate progress
            progress_data = {
                'target_amount': target_amount,
                'current_amount': initial_amount,
                'monthly_contribution': monthly_contribution,
                'progress_percentage': (initial_amount / target_amount * 100) if target_amount > 0 else 0,
            }

            capabilities.append(
                Capability(
                    capability_type=CapabilityType.SHOW_FORM,
                    data={
                        'form_type': 'fund_preview',
                        'fields': parameters,
                        'schema': self.get_parameter_schema(),
                        'progress': progress_data,
                    },
                    message='Xem trước quỹ tiết kiệm',
                ),
            )

        return capabilities

    # ========== Execution ==========

    async def execute(
        self,
        parameters: Dict[str, Any],
        context: Dict[str, Any],
    ) -> ExecutionResult:
        """Execute fund creation

        Works for both:
        1. Speech-to-input: Called by OrchestrationService after user confirms
        2. Traditional API: Called directly from /funds endpoint

        Required in context:
        - user_id: User creating the fund
        - fund_repository: SavingsFundRepository instance
        - account_repository: AccountRepository instance (if initial_amount > 0)
        """
        try:
            # Get repositories from context
            fund_repo = context.get('fund_repository')
            account_repo = context.get('account_repository')
            user_id = context.get('user_id')

            if not fund_repo or not user_id:
                return ExecutionResult(
                    success=False,
                    message='Missing required dependencies in context',
                    data={},
                )

            # Extract parameters
            fund_name = parameters['fund_name']
            target_amount = Decimal(str(parameters['target_amount']))
            target_date_str = parameters['target_date']
            initial_amount = Decimal(str(parameters.get('initial_amount', 0)))
            monthly_contribution = Decimal(str(parameters.get('monthly_contribution', 0)))
            category = parameters.get('category', self._suggest_category(fund_name))
            auto_transfer = parameters.get('auto_transfer', False)
            notes = parameters.get('notes', '')

            # Parse target_date
            if isinstance(target_date_str, str):
                for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']:
                    try:
                        target_date = datetime.strptime(target_date_str, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    return ExecutionResult(
                        success=False,
                        message=f'Định dạng ngày không hợp lệ: {target_date_str}',
                        data={},
                    )
            else:
                target_date = target_date_str

            # Get user's first account for initial deposit
            account_id = None
            if initial_amount > 0 and account_repo:
                user_accounts = await account_repo.get_by_user_id(int(user_id))
                if user_accounts:
                    account_id = int(user_accounts[0].account_id)

                    # Check balance
                    if Decimal(str(user_accounts[0].balance)) < initial_amount:
                        return ExecutionResult(
                            success=False,
                            message=f'Số dư không đủ để nạp tiền ban đầu. Số dư hiện tại: {user_accounts[0].balance:,} VND',
                            data={},
                        )

            # Create SavingsFund entity
            fund = SavingsFund(
                user_id=int(user_id),
                account_id=account_id,
                fund_name=fund_name,
                target_amount=target_amount,
                current_amount=Decimal('0.00'),  # Will be updated if initial_amount > 0
                currency='VND',
                target_date=target_date,
                category=category,
                monthly_contribution=monthly_contribution,
                auto_transfer=auto_transfer,
                notes=notes,
                status='active',
            )

            # Save to database
            created_fund = await fund_repo.create(fund)

            # If initial amount, deposit it
            deposit_message = ''
            if initial_amount > 0:
                # Deduct from account
                if account_repo and account_id:
                    await account_repo.update_balance(
                        account_id=account_id,
                        amount=initial_amount,
                        operation='subtract',
                    )

                # Deposit to fund
                updated_fund = await fund_repo.deposit(
                    fund_id=created_fund.fund_id,
                    amount=initial_amount,
                )
                created_fund = updated_fund
                deposit_message = f'. Đã nạp số tiền ban đầu: {initial_amount:,} VND'

            # Build message
            message = f'Đã tạo quỹ tiết kiệm "{fund_name}" với mục tiêu {target_amount:,} VND đến {target_date.strftime("%d/%m/%Y")}{deposit_message}'

            # Calculate progress
            progress_percentage = float(created_fund.current_amount / created_fund.target_amount * 100) if created_fund.target_amount > 0 else 0

            return ExecutionResult(
                success=True,
                message=message,
                data={
                    'fund_id': created_fund.fund_id,
                    'fund_name': created_fund.fund_name,
                    'target_amount': float(created_fund.target_amount),
                    'current_amount': float(created_fund.current_amount),
                    'target_date': created_fund.target_date.isoformat(),
                    'category': created_fund.category,
                    'monthly_contribution': float(created_fund.monthly_contribution),
                    'progress_percentage': round(progress_percentage, 2),
                    'status': created_fund.status,
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
                message=f'Có lỗi xảy ra khi tạo quỹ tiết kiệm: {str(e)}',
                data={},
            )
