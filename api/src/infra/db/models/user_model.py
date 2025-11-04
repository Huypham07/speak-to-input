from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import Numeric
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from .base_orm import BaseModel


class UserModel(BaseModel):
    __tablename__ = 'users'

    username: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Profile
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    # Timestamps
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def __repr__(self) -> str:
        return f'<User {self.username}>'


class AccountModel(BaseModel):
    """SQLAlchemy model for Account"""

    __tablename__ = 'accounts'

    user_id: Mapped[int] = mapped_column(
        nullable=False,
        index=True,
    )
    account_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )
    account_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Balance
    balance: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2),
        nullable=False,
        default=Decimal('0.00'),
    )
    currency: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default='VND',
    )

    # Type
    account_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default='checking',
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    def __repr__(self) -> str:
        return f'<Account {self.account_number}>'


class ContactModel(BaseModel):
    """SQLAlchemy model for Contact"""

    __tablename__ = 'contacts'

    user_id: Mapped[int] = mapped_column(
        nullable=False,
        index=True,
    )
    contact_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    account_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    bank_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    # Metadata
    is_favorite: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    def __repr__(self) -> str:
        return f'<Contact {self.contact_name}>'
