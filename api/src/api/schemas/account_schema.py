from __future__ import annotations

from typing import Optional

from pydantic import Field
from shared.base import BaseModel


class AccountResponse(BaseModel):
    """Account response schema"""
    id: int
    account_number: str
    account_name: str
    balance: float
    currency: str
    account_type: str
    is_active: bool


class DepositRequest(BaseModel):
    """Request to deposit money to account"""
    amount: float = Field(..., gt=0, description='Amount to deposit')
    note: Optional[str] = Field(None, description='Optional note')


class WithdrawRequest(BaseModel):
    """Request to withdraw money from account"""
    amount: float = Field(..., gt=0, description='Amount to withdraw')
    note: Optional[str] = Field(None, description='Optional note')


class TransactionResponse(BaseModel):
    """Transaction response schema"""
    transaction_id: str
    account_id: int
    transaction_type: str  # deposit, withdraw
    amount: float
    balance_after: float
    note: Optional[str]
    created_at: str
