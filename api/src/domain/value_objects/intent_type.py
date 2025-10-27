from __future__ import annotations

from enum import Enum


class IntentType(str, Enum):
    """Supported intent types"""

    # Structured intents
    ACCOUNT_OPENING = 'account_opening'
    SEND_MONEY = 'send_money'
    CHECK_BALANCE = 'check_balance'
    QUICK_ACTION = 'quick_action'

    # Complex intents
    CREATE_FUND = 'create_fund'
    CREATE_LOAN = 'create_loan'
    BUDGET_ALLOCATION = 'budget_allocation'
    QUERY_FINANCE = 'query_finance'

    # Meta intents
    UNKNOWN = 'unknown'
    CONFIRMATION = 'confirmation'
    CANCELLATION = 'cancellation'


class IntentCategory(str, Enum):
    """Intent categories for grouping"""

    TRANSACTION = 'transaction'
    ACCOUNT = 'account'
    INVESTMENT = 'investment'
    QUERY = 'query'
    META = 'meta'
