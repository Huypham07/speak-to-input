from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import Field
from shared.base import BaseModel


class Transaction(BaseModel):
    """Domain entity for financial Transaction"""

    user_id: int = Field(..., description='User who initiated the transaction')
    from_account_id: Optional[int] = Field(None, description='Source account ID')
    to_account_id: Optional[int] = Field(None, description='Destination account ID')

    # Transaction details
    transaction_type: str = Field(..., description='transfer, deposit, withdrawal')
    amount: Decimal = Field(..., description='Transaction amount')
    currency: str = Field(default='VND', description='Currency code')

    # Recipient info (for external transfers)
    recipient_account_number: Optional[str] = Field(None, description='External account number')
    recipient_name: Optional[str] = Field(None, description='Recipient name')
    recipient_bank: Optional[str] = Field(None, description='Recipient bank name')

    # Message and extra data
    message: Optional[str] = Field(None, description='Transaction message/note')
    extra_data: Optional[dict] = Field(None, description='Additional metadata')

    # Status
    status: str = Field(default='pending', description='pending, completed, failed, cancelled')

    # Timestamps
    created_at: Optional[datetime] = Field(None, description='Created timestamp')
    completed_at: Optional[datetime] = Field(None, description='Completion timestamp')


class Bill(BaseModel):
    """Domain entity for Bill payment"""

    user_id: int = Field(..., description='User who owns the bill')

    # Bill details
    bill_name: str = Field(..., description='Bill name/description')
    amount: Decimal = Field(..., description='Bill amount')
    currency: str = Field(default='VND', description='Currency code')

    # Due date
    due_date: datetime = Field(..., description='Bill due date')

    # Category
    category: Optional[str] = Field(None, description='utilities, rent, insurance, subscription, other')

    # Recurring
    is_recurring: bool = Field(default=False, description='Whether bill recurs')
    recurrence_interval: Optional[str] = Field(None, description='monthly, quarterly, yearly')

    # Reminder
    reminder_days: int = Field(default=3, description='Days before due date to remind')

    # Notes
    notes: Optional[str] = Field(None, description='Additional notes')

    # Status
    status: str = Field(default='pending', description='pending, paid, overdue, cancelled')
    paid_at: Optional[datetime] = Field(None, description='Payment timestamp')

    # Timestamps
    created_at: Optional[datetime] = Field(None, description='Created timestamp')
    updated_at: Optional[datetime] = Field(None, description='Updated timestamp')


class SavingsFund(BaseModel):
    """Domain entity for Savings Fund"""

    user_id: int = Field(..., description='User who owns the fund')
    account_id: Optional[int] = Field(None, description='Linked account ID')

    # Fund details
    fund_name: str = Field(..., description='Fund name/goal')
    target_amount: Decimal = Field(..., description='Target amount to save')
    current_amount: Decimal = Field(default=Decimal('0.00'), description='Current saved amount')
    currency: str = Field(default='VND', description='Currency code')

    # Target date
    target_date: datetime = Field(..., description='Target completion date')

    # Category
    category: Optional[str] = Field(None, description='travel, education, emergency, purchase, retirement, other')

    # Contribution
    monthly_contribution: Decimal = Field(default=Decimal('0.00'), description='Monthly contribution amount')
    auto_transfer: bool = Field(default=False, description='Enable automatic transfer')

    # Notes
    notes: Optional[str] = Field(None, description='Additional notes')

    # Status
    status: str = Field(default='active', description='active, completed, cancelled')
    completed_at: Optional[datetime] = Field(None, description='Completion timestamp')

    # Timestamps
    created_at: Optional[datetime] = Field(None, description='Created timestamp')
    updated_at: Optional[datetime] = Field(None, description='Updated timestamp')


class FundTransaction(BaseModel):
    """Domain entity for Fund Transaction (deposit/withdrawal)"""

    fund_id: int = Field(..., description='Associated fund ID')
    transaction_id: Optional[int] = Field(None, description='Linked transaction ID')

    # Transaction details
    transaction_type: str = Field(..., description='deposit or withdrawal')
    amount: Decimal = Field(..., description='Transaction amount')

    # Notes
    notes: Optional[str] = Field(None, description='Transaction notes')

    # Timestamp
    created_at: Optional[datetime] = Field(None, description='Created timestamp')
