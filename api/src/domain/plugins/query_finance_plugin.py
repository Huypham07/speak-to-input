from __future__ import annotations

from typing import Any
from typing import Dict

from domain.entities import ExecutionResult
from domain.value_objects import IntentType

from .base_intent_plugin import IntentPlugin


class QueryFinancePlugin(IntentPlugin):
    """Plugin for QUERY_FINANCE intent"""

    # ========== Metadata ==========

    @property
    def intent_type(self) -> str:
        return IntentType.QUERY_FINANCE.value

    @property
    def display_name(self) -> str:
        return 'Truy vấn tài chính'

    @property
    def description(self) -> str:
        return 'Query financial information including transactions, bills, funds'

    @property
    def requires_voice_confirmation(self) -> bool:
        """Read-only operation, no confirmation needed"""
        return False

    # ========== Parameter Schema ==========

    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            'type': 'object',
            'properties': {
                'query_type': {
                    'type': 'string',
                    'enum': ['transactions', 'bills', 'funds', 'summary'],
                    'description': 'Type of query',
                },
                'time_period': {
                    'type': 'string',
                    'enum': ['today', 'week', 'month', 'year'],
                    'description': 'Time period for query',
                },
                'limit': {
                    'type': 'integer',
                    'minimum': 1,
                    'maximum': 100,
                    'description': 'Number of results to return',
                },
            },
        }

    # ========== Execution ==========

    async def execute(
        self,
        parameters: Dict[str, Any],
        context: Dict[str, Any],
    ) -> ExecutionResult:
        """Query financial information

        Optional parameters:
        - query_type: Type of query (transactions/bills/funds/summary)
        - time_period: Time period filter
        - limit: Number of results

        Required in context:
        - user_id: User requesting info
        - transaction_repository: TransactionRepository instance
        - bill_repository: BillRepository instance
        - fund_repository: SavingsFundRepository instance
        """
        try:
            # Get dependencies
            transaction_repo = context.get('transaction_repository')
            bill_repo = context.get('bill_repository')
            fund_repo = context.get('fund_repository')
            user_id = context.get('user_id')

            if not all([transaction_repo, bill_repo, fund_repo, user_id]):
                return ExecutionResult(
                    success=False,
                    message='Missing required dependencies',
                    data={},
                )

            assert transaction_repo is not None
            assert bill_repo is not None
            assert fund_repo is not None
            assert user_id is not None

            query_type = parameters.get('query_type', 'summary')
            limit = parameters.get('limit', 10)

            result_data = {}
            message_parts = []

            if query_type == 'transactions' or query_type == 'summary':
                # Get recent transactions
                transactions = await transaction_repo.get_by_user_id(user_id, limit=limit)
                result_data['transactions'] = [
                    {
                        'id': t.id,
                        'type': t.transaction_type,
                        'amount': float(t.amount),
                        'description': t.description,
                        'created_at': t.created_at.isoformat() if t.created_at else None,
                    }
                    for t in transactions
                ]
                message_parts.append(f'{len(transactions)} giao dịch gần đây')

            if query_type == 'bills' or query_type == 'summary':
                # Get bills
                bills = await bill_repo.get_by_user_id(user_id)
                result_data['bills'] = [
                    {
                        'id': b.id,
                        'name': b.bill_name,
                        'amount': float(b.amount),
                        'due_date': b.due_date.isoformat() if b.due_date else None,
                        'status': b.status,
                    }
                    for b in bills[:limit]
                ]
                message_parts.append(f'{len(bills)} hóa đơn')

            if query_type == 'funds' or query_type == 'summary':
                # Get funds
                funds = await fund_repo.get_by_user_id(user_id)
                result_data['funds'] = [
                    {
                        'id': f.id,
                        'name': f.fund_name,
                        'current_amount': float(f.current_amount),
                        'target_amount': float(f.target_amount) if f.target_amount else None,
                    }
                    for f in funds[:limit]
                ]
                message_parts.append(f'{len(funds)} quỹ tiết kiệm')

            message = 'Thông tin tài chính: ' + ', '.join(message_parts)

            return ExecutionResult(
                success=True,
                message=message,
                data=result_data,
            )

        except Exception as e:
            return ExecutionResult(
                success=False,
                message=f'Lỗi khi truy vấn thông tin: {str(e)}',
                data={},
            )
