from __future__ import annotations

from datetime import date
from datetime import datetime
from decimal import Decimal
from typing import Annotated
from typing import Any
from typing import Dict
from typing import List
from typing import Literal
from typing import Optional

from domain.entities import AMBIGUOUSFieldError
from domain.entities import Bill
from domain.entities import BusinessState
from domain.entities import Capability
from domain.entities import ExecutionResult
from domain.entities import InvalidFieldError
from domain.entities import map_validation_errors
from domain.entities import MissingFieldError
from domain.entities import ValidationResult
from domain.value_objects import CapabilityType
from domain.value_objects import FieldStatus
from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator

from .base_intent_plugin import IntentPlugin


class BillValidation(BaseModel):
    bill_name: Annotated[
        str,
        Field(description='Bill name (e.g., "Tiền điện", "Tiền nước")', min_length=1, max_length=100),
    ]

    amount: Annotated[
        float,
        Field(description='Bill amount in VND', ge=1000, le=100_000_000),
    ]

    due_date: Annotated[
        datetime,
        Field(description='Due date (YYYY-MM-DD)'),
    ]

    category: Optional[
        Literal['utilities', 'rent', 'insurance', 'subscription', 'other']
    ] = Field(
        None,
        description='Bill category',
        json_schema_extra={
            'options': [
                {'value': 'utilities', 'label': 'Tiện ích (điện, nước, gas)'},
                {'value': 'rent', 'label': 'Tiền nhà'},
                {'value': 'insurance', 'label': 'Bảo hiểm'},
                {'value': 'subscription', 'label': 'Dịch vụ đăng ký'},
                {'value': 'other', 'label': 'Khác'},
            ],
        },
    )

    recurring: bool = Field(default=False, description='Whether bill recurs monthly')

    reminder_days: Annotated[
        int,
        Field(ge=0, le=30, description='Days before due date to remind'),
    ] = 3

    notes: Optional[
        Annotated[str, Field(max_length=500, description='Additional notes')]
    ] = None

    @staticmethod
    def _suggest_category(bill_name: str) -> str:
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

    @field_validator('bill_name')
    @classmethod
    def validate_bill_name(cls, v: Optional[str]):
        if v is None or not isinstance(v, str) or v.strip() == '':
            raise MissingFieldError('Tên hóa đơn bị thiếu hoặc là chuỗi rỗng.')
        if len(v) > 100:
            raise InvalidFieldError('Tên hóa đơn không được vượt quá 100 ký tự.')
        return v

    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v: float):
        MIN_AMOUNT = 1000
        MAX_AMOUNT = 100_000_000
        if v is None:
            raise MissingFieldError('Trường "amount" bị thiếu hoặc None.')

        if v < MIN_AMOUNT or v > MAX_AMOUNT:
            raise InvalidFieldError('Số tiền hóa đơn phải nằm trong khoảng từ 1.000 đến 100.000.000 VND.')

        return v

    @field_validator('due_date', mode='before')
    @classmethod
    def validate_due_date(cls, v: str) -> datetime:
        if v is None or not v.strip():
            raise MissingFieldError('Trường "due_date" bị thiếu hoặc None.')
        try:
            date_object = datetime.fromisoformat(v)
            today = date.today()
            if date_object < today:
                raise InvalidFieldError(f'Ngày đến hạn ({date_object}) không thể là ngày trong quá khứ.')
        except Exception:
            raise InvalidFieldError(f'Ngày đến hạn ({date_object}) Phải Đúng chuẩn format YYYY-MM-DD')
        return date_object

    @field_validator('category', mode='after')
    @classmethod
    def validate_category_ambiguity(cls, v: Optional[str], info):
        if v is None:
            bill_name = info.data.get('bill_name')
            if bill_name:
                suggested = cls._suggest_category(bill_name)
                raise AMBIGUOUSFieldError(
                    f'Thiếu category, nhưng có thể gợi ý: "{suggested}". '
                    f'Vui lòng xác nhận rõ loại hóa đơn.',
                )
            else:
                raise MissingFieldError('Thiếu category và không thể xác định từ bill_name.')
        return v


class CreateBillPlugin(IntentPlugin):
    """Plugin for CREATE_BILL intent"""

    def __init__(self):
        self._bill_repo = None

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
        return BillValidation.model_json_schema()

    # ========== Validation ==========

    def validate_parameters(
        self,
        parameters: Dict[str, Any],
        context: Dict[str, Any],
    ) -> ValidationResult:
        """Validate bill parameters"""
        parameters['category'] = parameters.get('category', None)
        results = map_validation_errors(data=parameters, model=BillValidation)

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

    # ========== Capability Resolution ==========

    def resolve_capabilities(
        self,
        parameters: Dict[str, Any],
        validation_result: ValidationResult,
        state: BusinessState,
    ) -> List[Capability]:
        """Resolve capabilities for bill creation"""
        capabilities = []

        if validation_result.missing_fields:
            for field in validation_result.missing_fields:
                capabilities.append(
                    Capability(
                        capability_type=CapabilityType.REQUEST_INPUT,
                        priority=1,
                        data={
                            'field': field.field_name,
                            'message': field.error_message,
                        },
                    ),
                )
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
            category = parameters.get('category', BillValidation._suggest_category(bill_name))
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
