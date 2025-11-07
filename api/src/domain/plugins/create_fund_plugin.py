from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from typing import Dict

from domain.entities import ExecutionResult
from domain.entities import SavingsFund
from domain.entities import Transaction
from domain.value_objects import IntentType

from .base_intent_plugin import IntentPlugin


class CreateFundPlugin(IntentPlugin):
    """Plugin for CREATE_FUND intent"""

    # ========== Metadata ==========

    @property
    def intent_type(self) -> str:
        return IntentType.CREATE_FUND.value

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

    # ========== Execution ==========

    async def execute(
        self,
        parameters: Dict[str, Any],
        context: Dict[str, Any],
    ) -> ExecutionResult:
        """Execute fund creation"""
        try:
            # Get repositories from context
            fund_repo = context.get('fund_repository')
            account_repo = context.get('account_repository')
            transaction_repo = context.get('transaction_repository')
            user_id = context.get('user_id')

            if not all([fund_repo, account_repo, transaction_repo, user_id]):
                return ExecutionResult(
                    success=False,
                    message='Missing required dependencies in context',
                    data={},
                )

            # Type assertions after null check
            assert fund_repo is not None
            assert transaction_repo is not None
            assert account_repo is not None
            assert user_id is not None

            # Validate and extract parameters
            fund_name = parameters.get('fund_name', '').strip()
            if not fund_name:
                return ExecutionResult(
                    success=False,
                    message='Tên quỹ là bắt buộc',
                    data={},
                )

            target_amount = parameters.get('target_amount')
            if not target_amount:
                return ExecutionResult(
                    success=False,
                    message='Số tiền mục tiêu là bắt buộc',
                    data={},
                )
            if target_amount < 100000:
                return ExecutionResult(
                    success=False,
                    message='Số tiền mục tiêu phải từ 100,000 VND trở lên',
                    data={},
                )
            target_amount = Decimal(str(target_amount))

            target_date_str = parameters.get('target_date')
            if not target_date_str:
                return ExecutionResult(
                    success=False,
                    message='Ngày mục tiêu là bắt buộc',
                    data={},
                )

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

            # Optional parameters
            initial_amount = Decimal(str(parameters.get('initial_amount', 0)))
            monthly_contribution = Decimal(str(parameters.get('monthly_contribution', 0)))
            category = parameters.get('category', 'other')
            auto_transfer = parameters.get('auto_transfer', False)
            notes = parameters.get('notes', '')

            # Get user's first account for initial deposit
            account_id = None
            if initial_amount > 0:
                user_accounts = await account_repo.get_by_user_id(int(user_id))
                if user_accounts:
                    account_id = int(user_accounts[0].id)

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
                if account_id:
                    await account_repo.update_balance(
                        account_id=account_id,
                        amount=initial_amount,
                        operation='subtract',
                    )

                # Deposit to fund
                updated_fund = await fund_repo.deposit(
                    fund_id=created_fund.id,
                    amount=initial_amount,
                )
                created_fund = updated_fund
                # Create transaction record for initial deposit
                # From account perspective: money goes out (withdraw from account)
                transaction = Transaction(
                    user_id=int(user_id),
                    from_account_id=account_id,
                    to_account_id=None,  # Fund is not an account
                    transaction_type='withdraw',  # From account perspective: money withdrawn
                    amount=initial_amount,
                    currency='VND',
                    message=f'Nạp tiền ban đầu vào quỹ "{fund_name}"',
                    status='completed',
                    extra_data={
                        'fund_id': created_fund.id,
                        'fund_name': fund_name,
                        'transaction_category': 'fund_initial_deposit',
                    },
                )
                await transaction_repo.create(transaction)

                deposit_message = f'. Đã nạp số tiền ban đầu: {initial_amount:,} VND'

            # Build message
            message = f'Đã tạo quỹ tiết kiệm "{fund_name}" với mục tiêu {target_amount:,} VND đến {target_date.strftime("%d/%m/%Y")}{deposit_message}'

            # Calculate progress
            progress_percentage = float(created_fund.current_amount / created_fund.target_amount * 100) if created_fund.target_amount > 0 else 0

            return ExecutionResult(
                success=True,
                message=message,
                data={
                    'fund_id': created_fund.id,
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
