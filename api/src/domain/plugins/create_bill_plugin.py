from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from typing import Dict
from typing import List

from domain.entities import Bill
from domain.entities import BusinessState
from domain.entities import Capability
from domain.entities import ExecutionResult
from domain.entities import FieldValidation
from domain.entities import ValidationResult
from domain.value_objects import CapabilityType
from domain.value_objects import FieldStatus

from .base_intent_plugin import IntentPlugin


class CreateBillPlugin(IntentPlugin):
    """Plugin for CREATE_BILL intent"""

    # ========== Metadata ==========

    @property
    def intent_type(self) -> str:
        return 'CREATE_BILL'

    @property
    def display_name(self) -> str:
        return 'Tạo hóa đơn'

    @property
    def description(self) -> str:
        return 'Create a new bill/payment reminder'

    # ========== Parameter Schema ==========

    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            'type': 'object',
            'required': ['bill_name', 'amount', 'due_date'],
            'properties': {
                'bill_name': {
                    'type': 'string',
                    'description': 'Bill name (e.g., "Tiền điện", "Tiền nước")',
                    'minLength': 1,
                    'maxLength': 100,
                },
                'amount': {
                    'type': 'number',
                    'minimum': 1000,
                    'maximum': 100000000,
                    'description': 'Bill amount in VND',
                },
                'due_date': {
                    'type': 'string',
                    'format': 'date',
                    'description': 'Due date (YYYY-MM-DD)',
                },
                'category': {
                    'type': 'string',
                    'enum': ['utilities', 'rent', 'insurance', 'subscription', 'other'],
                    'description': 'Bill category',
                },
                'recurring': {
                    'type': 'boolean',
                    'description': 'Whether bill recurs monthly',
                    'default': False,
                },
                'reminder_days': {
                    'type': 'integer',
                    'minimum': 0,
                    'maximum': 30,
                    'description': 'Days before due date to remind',
                    'default': 3,
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
        """Validate bill parameters"""
        results = []

        # Validate bill_name
        bill_name = parameters.get('bill_name')
        if not bill_name:
            results.append(
                FieldValidation(
                    field_name='bill_name',
                    status=FieldStatus.MISSING,
                    confidence=0.0,
                ),
            )
        elif len(bill_name.strip()) < 1:
            results.append(
                FieldValidation(
                    field_name='bill_name',
                    status=FieldStatus.INVALID,
                    value=bill_name,
                    confidence=0.0,
                    error_message='Tên hóa đơn không được để trống',
                ),
            )
        else:
            results.append(
                FieldValidation(
                    field_name='bill_name',
                    status=FieldStatus.VALID,
                    value=bill_name,
                    confidence=1.0,
                ),
            )

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
        elif amount < 1000 or amount > 100000000:
            results.append(
                FieldValidation(
                    field_name='amount',
                    status=FieldStatus.INVALID,
                    value=amount,
                    confidence=0.0,
                    error_message='Số tiền phải từ 1,000 đến 100,000,000 VND',
                ),
            )
        else:
            results.append(
                FieldValidation(
                    field_name='amount',
                    status=FieldStatus.VALID,
                    value=amount,
                    confidence=1.0,
                ),
            )

        # Validate due_date
        due_date = parameters.get('due_date')
        if not due_date:
            results.append(
                FieldValidation(
                    field_name='due_date',
                    status=FieldStatus.MISSING,
                    confidence=0.0,
                ),
            )
        else:
            # TODO: Validate date format and ensure it's in the future
            results.append(
                FieldValidation(
                    field_name='due_date',
                    status=FieldStatus.VALID,
                    value=due_date,
                    confidence=1.0,
                ),
            )

        # Validate category (optional, suggest if missing)
        category = parameters.get('category')
        if not category and bill_name:
            # Suggest category based on bill_name
            suggested_category = self._suggest_category(bill_name)
            if suggested_category:
                results.append(
                    FieldValidation(
                        field_name='category',
                        status=FieldStatus.AMBIGUOUS,
                        value=suggested_category,
                        confidence=0.7,
                        metadata={
                            'options': [
                                {'value': 'utilities', 'label': 'Tiện ích (điện, nước, gas)'},
                                {'value': 'rent', 'label': 'Tiền nhà'},
                                {'value': 'insurance', 'label': 'Bảo hiểm'},
                                {'value': 'subscription', 'label': 'Dịch vụ đăng ký'},
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

        # Determine overall validity
        is_valid = all(
            r.status == FieldStatus.VALID or r.field_name == 'category'
            for r in results
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

    def _suggest_category(self, bill_name: str) -> str:
        """Suggest category based on bill name"""
        if not bill_name:
            return 'other'

        name_lower = bill_name.lower()

        if any(word in name_lower for word in ['điện', 'nước', 'gas', 'internet', 'điện thoại']):
            return 'utilities'
        elif any(word in name_lower for word in ['nhà', 'rent', 'thuê']):
            return 'rent'
        elif any(word in name_lower for word in ['bảo hiểm', 'insurance']):
            return 'insurance'
        elif any(word in name_lower for word in ['netflix', 'spotify', 'đăng ký', 'subscription']):
            return 'subscription'
        else:
            return 'other'

    # ========== Capability Resolution ==========

    def resolve_capabilities(
        self,
        parameters: Dict[str, Any],
        validation_result: ValidationResult,
        state: BusinessState,
    ) -> List[Capability]:
        """Resolve capabilities for bill creation"""
        capabilities = []

        # If all required fields are valid, show preview
        if validation_result.is_valid:
            capabilities.append(
                Capability(
                    capability_type=CapabilityType.SHOW_FORM,
                    data={
                        'form_type': 'bill_preview',
                        'fields': parameters,
                        'schema': self.get_parameter_schema(),
                    },
                    message='Xem trước hóa đơn',
                ),
            )

        return capabilities

    # ========== Execution ==========

    async def execute(
        self,
        parameters: Dict[str, Any],
        context: Dict[str, Any],
    ) -> ExecutionResult:
        """Execute bill creation

        Works for both:
        1. Speech-to-input: Called by OrchestrationService after user confirms
        2. Traditional API: Called directly from /bills endpoint

        Required in context:
        - user_id: User creating the bill
        - bill_repository: BillRepository instance
        """
        try:
            # Get repository from context
            bill_repo = context.get('bill_repository')
            user_id = context.get('user_id')

            if not bill_repo or not user_id:
                return ExecutionResult(
                    success=False,
                    message='Missing required dependencies in context',
                    data={},
                )

            # Extract parameters
            bill_name = parameters['bill_name']
            amount = Decimal(str(parameters['amount']))
            due_date_str = parameters['due_date']
            category = parameters.get('category', self._suggest_category(bill_name))
            is_recurring = parameters.get('recurring', False)
            reminder_days = parameters.get('reminder_days', 3)
            notes = parameters.get('notes', '')

            # Parse due_date
            if isinstance(due_date_str, str):
                # Try multiple date formats
                for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']:
                    try:
                        due_date = datetime.strptime(due_date_str, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    return ExecutionResult(
                        success=False,
                        message=f'Định dạng ngày không hợp lệ: {due_date_str}',
                        data={},
                    )
            else:
                due_date = due_date_str

            # Create Bill entity
            bill = Bill(
                user_id=int(user_id),
                bill_name=bill_name,
                amount=amount,
                currency='VND',
                due_date=due_date,
                category=category,
                is_recurring=is_recurring,
                recurrence_interval='monthly' if is_recurring else None,
                reminder_days=reminder_days,
                notes=notes,
                status='pending',
            )

            # Save to database
            created_bill = await bill_repo.create(bill)

            return ExecutionResult(
                success=True,
                message=f'Đã tạo hóa đơn "{bill_name}" với số tiền {amount:,} VND, hạn thanh toán {due_date.strftime("%d/%m/%Y")}',
                data={
                    'bill_id': created_bill.bill_id,
                    'bill_name': created_bill.bill_name,
                    'amount': float(created_bill.amount),
                    'due_date': created_bill.due_date.isoformat(),
                    'category': created_bill.category,
                    'is_recurring': created_bill.is_recurring,
                    'status': created_bill.status,
                },
            )

        except Exception as e:
            return ExecutionResult(
                success=False,
                message=f'Có lỗi xảy ra khi tạo hóa đơn: {str(e)}',
                data={},
            )
