from __future__ import annotations

from enum import Enum


class IntentType(str, Enum):
    """Supported intent types"""

    # Transaction intents
    SEND_MONEY = 'SEND_MONEY'

    # Financial management intents
    CREATE_BILL = 'CREATE_BILL'
    CREATE_FUND = 'CREATE_FUND'
    DEPOSIT_FUND = 'DEPOSIT_FUND'
    WITHDRAW_FUND = 'WITHDRAW_FUND'
    DELETE_FUND = 'DELETE_FUND'

    # Query intents
    CHECK_BALANCE = 'CHECK_BALANCE'
    QUERY_FINANCE = 'QUERY_FINANCE'

    # Account intents
    ACCOUNT_OPENING = 'ACCOUNT_OPENING'

    # Other intents
    QUICK_ACTION = 'QUICK_ACTION'
    CREATE_LOAN = 'CREATE_LOAN'
    BUDGET_ALLOCATION = 'BUDGET_ALLOCATION'

    # Meta intents
    UNKNOWN = 'UNKNOWN'
    CONFIRMATION = 'CONFIRMATION'
    CANCELLATION = 'CANCELLATION'


class IntentCategory(str, Enum):
    """Intent categories for grouping"""

    TRANSACTION = 'transaction'
    ACCOUNT = 'account'
    INVESTMENT = 'investment'
    QUERY = 'query'
    META = 'meta'
