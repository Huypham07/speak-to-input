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


class OtherUserAccountResponse(BaseModel):
    """Account response schema with user info for other users' accounts"""
    id: int
    account_number: str
    account_name: str
    balance: float
    currency: str
    account_type: str
    is_active: bool
    user_id: int
    user_full_name: str
    user_username: str


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
    id: int
    user_id: int
    from_account_id: Optional[int] = None
    to_account_id: Optional[int] = None
    transaction_type: str  # deposit, withdraw, transfer
    amount: float
    currency: str
    status: str
    message: Optional[str] = None
    recipient_account_number: Optional[str] = None
    recipient_name: Optional[str] = None
    recipient_bank: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None
