from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from typing import Dict

from domain.entities import Bill
from domain.entities import ExecutionResult
from domain.value_objects import IntentType

from .base_intent_plugin import IntentPlugin


class CreateBillPlugin(IntentPlugin):
    """Plugin for CREATE_BILL intent"""

    # ========== Metadata ==========

    @property
    def intent_type(self) -> str:
        return IntentType.CREATE_BILL.value

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

    # ========== Execution ==========

    async def execute(
        self,
        parameters: Dict[str, Any],
        context: Dict[str, Any],
    ) -> ExecutionResult:
        """Execute bill creation with inline validation

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

            # Validate and extract parameters
            bill_name = parameters.get('bill_name', '').strip()
            if not bill_name:
                return ExecutionResult(
                    success=False,
                    message='Tên hóa đơn là bắt buộc',
                    data={},
                )

            amount = parameters.get('amount')
            if not amount:
                return ExecutionResult(
                    success=False,
                    message='Số tiền là bắt buộc',
                    data={},
                )
            if amount < 1000 or amount > 100000000:
                return ExecutionResult(
                    success=False,
                    message='Số tiền phải từ 1,000 đến 100,000,000 VND',
                    data={},
                )
            amount = Decimal(str(amount))

            due_date_str = parameters.get('due_date')
            if not due_date_str:
                return ExecutionResult(
                    success=False,
                    message='Ngày hết hạn là bắt buộc',
                    data={},
                )

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

            # Optional parameters
            category = parameters.get('category', 'other')
            is_recurring = parameters.get('recurring', False)
            reminder_days = parameters.get('reminder_days', 3)
            notes = parameters.get('notes', '')

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
