from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import Field
from shared.base import BaseModel


class User(BaseModel):
    """Domain entity for User"""
    username: str = Field(..., description='Username for login')
    email: str = Field(..., description='User email')
    hashed_password: str = Field(..., description='Hashed password')

    # Profile
    full_name: str = Field(..., description='Full name')
    phone: Optional[str] = Field(None, description='Phone number')

    # Status
    is_active: bool = Field(default=True, description='Whether user is active')
    is_verified: bool = Field(default=False, description='Whether email is verified')

    # Timestamps
    last_login: Optional[datetime] = Field(None, description='Last login timestamp')


class Account(BaseModel):
    """Domain entity for financial Account"""

    account_id: str = Field(..., description='Unique account identifier')
    user_id: int = Field(..., description='Owner user ID')
    account_number: str = Field(..., description='Account number')
    account_name: str = Field(..., description='Account name/label')

    # Balance
    balance: float = Field(default=0.0, description='Current balance')
    currency: str = Field(default='VND', description='Currency code')

    # Type
    account_type: str = Field(default='checking', description='Account type')

    # Status
    is_active: bool = Field(default=True, description='Whether account is active')


class Contact(BaseModel):
    """Domain entity for transfer Contact"""

    contact_id: str = Field(..., description='Unique contact identifier')
    user_id: int = Field(..., description='Owner user ID')
    contact_name: str = Field(..., description='Contact display name')
    account_number: str = Field(..., description='Contact account number')
    bank_name: Optional[str] = Field(None, description='Bank name')

    # Metadata
    is_favorite: bool = Field(default=False, description='Whether contact is favorite')
