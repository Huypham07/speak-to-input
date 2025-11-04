from __future__ import annotations

from domain.entities.execution_result import ExecutionResult
from domain.plugins.registry import get_intent_plugin
from domain.value_objects import IntentType


async def execute_send_money(
    user_id: int,
    amount: float,
    recipient: str,
    message: str = '',
    # Repositories
    transaction_repository=None,
    account_repository=None,
    contact_repository=None,
) -> ExecutionResult:
    """Execute send money via plugin

    This is called from:
    1. OrchestrationService (speech-to-input flow)
    2. POST /api/v1/transfers (traditional API)
    """
    plugin = get_intent_plugin(IntentType.SEND_MONEY.value)

    if not plugin:
        return ExecutionResult(
            success=False,
            message='Send money plugin not found',
            data={},
        )

    parameters = {
        'amount': amount,
        'recipient': recipient,
        'message': message,
    }

    context = {
        'user_id': user_id,
        'transaction_repository': transaction_repository,
        'account_repository': account_repository,
        'contact_repository': contact_repository,
    }

    return await plugin.execute(parameters, context)


async def execute_create_bill(
    user_id: int,
    bill_name: str,
    amount: float,
    due_date: str,
    category: str,
    recurring: bool = False,
    reminder_days: int = 3,
    notes: str = '',
    # Repository
    bill_repository=None,
) -> ExecutionResult:
    """Execute create bill via plugin

    This is called from:
    1. OrchestrationService (speech-to-input flow)
    2. POST /api/v1/bills (traditional API)
    """
    plugin = get_intent_plugin(IntentType.CREATE_BILL.value)

    if not plugin:
        return ExecutionResult(
            success=False,
            message='Create bill plugin not found',
            data={},
        )

    parameters = {
        'bill_name': bill_name,
        'amount': amount,
        'due_date': due_date,
        'category': category,
        'recurring': recurring,
        'reminder_days': reminder_days,
        'notes': notes,
    }

    context = {
        'user_id': user_id,
        'bill_repository': bill_repository,
    }

    return await plugin.execute(parameters, context)


async def execute_create_fund(
    user_id: int,
    fund_name: str,
    target_amount: float,
    target_date: str,
    category: str,
    initial_amount: float = 0,
    monthly_contribution: float = 0,
    auto_transfer: bool = False,
    notes: str = '',
    # Repositories
    fund_repository=None,
    account_repository=None,
) -> ExecutionResult:
    """Execute create savings fund via plugin

    This is called from:
    1. OrchestrationService (speech-to-input flow)
    2. POST /api/v1/funds (traditional API)
    """
    plugin = get_intent_plugin(IntentType.CREATE_FUND.value)

    if not plugin:
        return ExecutionResult(
            success=False,
            message='Create fund plugin not found',
            data={},
        )

    parameters = {
        'fund_name': fund_name,
        'target_amount': target_amount,
        'target_date': target_date,
        'initial_amount': initial_amount,
        'monthly_contribution': monthly_contribution,
        'category': category,
        'auto_transfer': auto_transfer,
        'notes': notes,
    }

    context = {
        'user_id': user_id,
        'fund_repository': fund_repository,
        'account_repository': account_repository,
    }

    return await plugin.execute(parameters, context)


async def execute_deposit_fund(
    user_id: int,
    fund_id: int,
    amount: float,
    from_account_id: int | None = None,
    # Repositories
    fund_repository=None,
    account_repository=None,
) -> ExecutionResult:
    """Execute deposit to fund via plugin

    This is called from:
    1. OrchestrationService (speech-to-input flow)
    2. POST /api/v1/funds/{fund_id}/deposit (traditional API)
    """
    plugin = get_intent_plugin(IntentType.DEPOSIT_FUND.value)

    if not plugin:
        return ExecutionResult(
            success=False,
            message='Deposit fund plugin not found',
            data={},
        )

    parameters = {
        'fund_id': fund_id,
        'amount': amount,
    }
    if from_account_id:
        parameters['from_account_id'] = from_account_id

    context = {
        'user_id': user_id,
        'fund_repository': fund_repository,
        'account_repository': account_repository,
    }

    return await plugin.execute(parameters, context)


async def execute_withdraw_fund(
    user_id: int,
    fund_id: int,
    amount: float,
    to_account_id: int | None = None,
    # Repositories
    fund_repository=None,
    account_repository=None,
) -> ExecutionResult:
    """Execute withdraw from fund via plugin

    This is called from:
    1. OrchestrationService (speech-to-input flow)
    2. POST /api/v1/funds/{fund_id}/withdraw (traditional API)
    """
    plugin = get_intent_plugin(IntentType.WITHDRAW_FUND.value)

    if not plugin:
        return ExecutionResult(
            success=False,
            message='Withdraw fund plugin not found',
            data={},
        )

    parameters = {
        'fund_id': fund_id,
        'amount': amount,
    }
    if to_account_id:
        parameters['to_account_id'] = to_account_id

    context = {
        'user_id': user_id,
        'fund_repository': fund_repository,
        'account_repository': account_repository,
    }

    return await plugin.execute(parameters, context)


async def execute_delete_fund(
    user_id: int,
    fund_id: int,
    # Repository
    fund_repository=None,
) -> ExecutionResult:
    """Execute delete fund via plugin

    This is called from:
    1. OrchestrationService (speech-to-input flow)
    2. DELETE /api/v1/funds/{fund_id} (traditional API)
    """
    plugin = get_intent_plugin(IntentType.DELETE_FUND.value)

    if not plugin:
        return ExecutionResult(
            success=False,
            message='Delete fund plugin not found',
            data={},
        )

    parameters = {
        'fund_id': fund_id,
    }

    context = {
        'user_id': user_id,
        'fund_repository': fund_repository,
    }

    return await plugin.execute(parameters, context)
