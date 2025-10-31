from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Numeric
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from .base_orm import BaseModel


class TransactionModel(BaseModel):

    __tablename__ = 'transactions'

    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    from_account_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey('accounts.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
    )
    to_account_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey('accounts.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
    )

    # Transaction details
    transaction_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default='VND',
    )

    # Recipient info (for external transfers)
    recipient_account_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    recipient_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    recipient_bank: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    # Message and extra data
    message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    extra_data: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default='pending',
        index=True,
    )

    # Timestamps
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def __repr__(self) -> str:
        return f'<Transaction {self.id} {self.transaction_type} {self.amount}>'


class BillModel(BaseModel):

    __tablename__ = 'bills'

    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )

    # Bill details
    bill_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default='VND',
    )

    # Due date
    due_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    # Category
    category: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )

    # Recurring
    is_recurring: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    recurrence_interval: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )

    # Reminder
    reminder_days: Mapped[int] = mapped_column(
        nullable=False,
        default=3,
    )

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default='pending',
        index=True,
    )
    paid_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def __repr__(self) -> str:
        return f'<Bill {self.id} {self.bill_name}>'


class SavingsFundModel(BaseModel):

    __tablename__ = 'savings_funds'

    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    account_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey('accounts.id', ondelete='SET NULL'),
        nullable=True,
    )

    # Fund details
    fund_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    target_amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
    )
    current_amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        default=Decimal('0.00'),
    )
    currency: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default='VND',
    )

    # Target date
    target_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    # Category
    category: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )

    # Contribution
    monthly_contribution: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        default=Decimal('0.00'),
    )
    auto_transfer: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default='active',
        index=True,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def __repr__(self) -> str:
        return f'<SavingsFund {self.id} {self.fund_name}>'


class FundTransactionModel(BaseModel):

    __tablename__ = 'fund_transactions'

    fund_id: Mapped[int] = mapped_column(
        ForeignKey('savings_funds.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    transaction_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey('transactions.id', ondelete='SET NULL'),
        nullable=True,
    )

    # Transaction details
    transaction_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
    )

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    def __repr__(self) -> str:
        return f'<FundTransaction {self.id} {self.transaction_type} {self.amount}>'
