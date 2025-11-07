from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import ConfigDict
from pydantic import Field
from shared.base import BaseModel


# ========== Transfer Schemas ==========

class TransferRequest(BaseModel):
    """Request to transfer money"""
    from_account_id: Optional[int] = Field(None, description='Source account ID, if None use default')
    recipient_account_number: str = Field(..., description='Recipient account number')
    recipient_name: Optional[str] = None
    amount: float = Field(..., gt=0)
    message: Optional[str] = None


class TransferResponse(BaseModel):
    """Transfer response"""
    id: int
    from_account_id: int
    to_account_number: str
    amount: float
    message: Optional[str]
    status: str
    created_at: str


# ========== Bill Schemas ==========

class CreateBillRequest(BaseModel):
    """Request to create a bill"""
    bill_name: str = Field(..., min_length=1, max_length=200)
    category: str
    amount: float = Field(..., gt=0)
    due_date: str = Field(..., description='Due date in YYYY-MM-DD format')
    notes: Optional[str] = None
    recurring: bool = Field(False)
    recurring_interval: Optional[str] = Field(None, description='daily, weekly, monthly, yearly')


class BillResponse(BaseModel):
    """Bill response"""
    id: int
    bill_name: str
    category: Optional[str] = None
    amount: float
    due_date: datetime
    status: str  # pending, paid, overdue
    notes: Optional[str] = None
    is_recurring: bool = False
    recurrence_interval: Optional[str] = None
    reminder_days: int = 3
    paid_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


# ========== Savings Fund Schemas ==========

class CreateFundRequest(BaseModel):
    """Request to create a savings fund"""
    fund_name: str = Field(..., min_length=1, max_length=100)
    target_amount: float = Field(..., gt=0)
    target_date: str = Field(..., description='Target date in YYYY-MM-DD format')
    initial_amount: float = Field(0, ge=0)
    monthly_contribution: float = Field(0, ge=0)
    category: Optional[str] = None
    auto_transfer: bool = Field(False)
    notes: Optional[str] = None


class FundResponse(BaseModel):
    """Fund response"""
    id: int
    fund_name: str
    target_amount: float
    current_amount: float
    target_date: str
    category: Optional[str]
    monthly_contribution: float
    progress_percentage: float
    status: str
    created_at: str


class FundDepositRequest(BaseModel):
    """Request to deposit to fund"""
    amount: float = Field(..., gt=0)
    from_account_id: Optional[int] = None  # If None, use default account


class FundWithdrawRequest(BaseModel):
    """Request to withdraw from fund"""
    amount: float = Field(..., gt=0)
    to_account_id: Optional[int] = None  # If None, use default account


# ========== Contact Schemas ==========

class ContactResponse(BaseModel):
    """Contact response"""
    id: int
    contact_name: str
    account_number: str
    bank_name: Optional[str]
    is_favorite: bool
