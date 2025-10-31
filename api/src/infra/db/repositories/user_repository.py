from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Callable
from typing import Optional

from infra.db.models import AccountModel
from infra.db.models import ContactModel
from infra.db.models import UserModel
from shared.exceptions import NotFoundError
from sqlalchemy import select
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from .base_repository import BaseRepository


class UserRepository(BaseRepository):
    """Repository for User management"""

    def __init__(self, session_factory: Callable[[], AsyncSession]):
        super().__init__(session_factory, UserModel)

    async def get_by_username(self, username: str) -> Optional[UserModel]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(UserModel).where(UserModel.username == username),
            )
            return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[UserModel]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(UserModel).where(UserModel.email == email),
            )
            return result.scalar_one_or_none()

    async def update_last_login(self, user_id: int) -> None:
        """Update user's last login timestamp"""
        async with self.session_factory() as session:
            await session.execute(
                update(UserModel)
                .where(UserModel.id == user_id)
                .values(last_login=datetime.now()),
            )
            await session.commit()


class AccountRepository(BaseRepository):
    """Repository for Account management"""

    def __init__(self, session_factory: Callable[[], AsyncSession]):
        super().__init__(session_factory, AccountModel)

    async def get_by_user_id(self, user_id: int) -> list[AccountModel]:
        """Get all accounts for a user"""
        async with self.session_factory() as session:
            result = await session.execute(
                select(AccountModel).where(AccountModel.user_id == user_id),
            )
            return result.scalars().all()

    async def count_by_user_id(self, user_id: int) -> int:
        """Count total accounts for a user"""
        async with self.session_factory() as session:
            result = await session.execute(
                select(AccountModel).where(AccountModel.user_id == user_id),
            )
            return len(result.scalars().all())

    async def get_by_account_number(self, account_number: str) -> Optional[AccountModel]:
        """Get account by account number"""
        async with self.session_factory() as session:
            result = await session.execute(
                select(AccountModel).where(AccountModel.account_number == account_number),
            )
            return result.scalar_one_or_none()

    async def update_balance(self, account_id: int, amount: Decimal, operation: str = 'add') -> AccountModel:
        """Update account balance

        Args:
            account_id: Account ID
            amount: Amount to add/subtract
            operation: 'add' or 'subtract'
        """
        async with self.session_factory() as session:
            result = await session.execute(
                select(AccountModel).where(AccountModel.id == account_id),
            )
            model = result.scalar_one_or_none()

            if not model:
                raise NotFoundError(detail=f'Account {account_id} not found')

            if operation == 'add':
                model.balance += amount
            elif operation == 'subtract':
                if model.balance < amount:
                    raise ValueError('Insufficient balance')
                model.balance -= amount
            else:
                raise ValueError(f'Invalid operation: {operation}')

            await session.commit()
            await session.refresh(model)

            return model

    async def transfer(
        self,
        from_account_id: int,
        to_account_id: int,
        amount: Decimal,
    ) -> tuple[AccountModel, AccountModel]:
        """Transfer money between accounts (atomic transaction)"""
        async with self.session_factory() as session:
            # Get both accounts
            result = await session.execute(
                select(AccountModel).where(
                    AccountModel.id.in_([from_account_id, to_account_id]),
                ),
            )
            models = {model.id: model for model in result.scalars().all()}

            if from_account_id not in models:
                raise NotFoundError(detail=f'Source account {from_account_id} not found')
            if to_account_id not in models:
                raise NotFoundError(detail=f'Destination account {to_account_id} not found')

            from_account = models[from_account_id]
            to_account = models[to_account_id]

            # Check balance
            if from_account.balance < amount:
                raise ValueError('Insufficient balance')

            # Perform transfer
            from_account.balance -= amount
            to_account.balance += amount

            await session.commit()
            await session.refresh(from_account)
            await session.refresh(to_account)

            return from_account, to_account


class ContactRepository(BaseRepository):
    """Repository for Contact management"""

    def __init__(self, session_factory: Callable[[], AsyncSession]):
        super().__init__(session_factory, ContactModel)

    async def get_by_user_id(self, user_id: int) -> list[ContactModel]:
        """Get all contacts for a user"""
        async with self.session_factory() as session:
            result = await session.execute(
                select(ContactModel).where(ContactModel.user_id == user_id),
            )
            return result.scalars().all()

    async def search_by_name(self, user_id: int, name: str) -> list[ContactModel]:
        """Search contacts by name (fuzzy match)"""
        async with self.session_factory() as session:
            result = await session.execute(
                select(ContactModel).where(
                    ContactModel.user_id == user_id,
                    ContactModel.contact_name.ilike(f'%{name}%'),
                ),
            )
            return result.scalars().all()

    async def get_by_account_number(self, user_id: int, account_number: str) -> Optional[ContactModel]:
        """Get contact by account number"""
        async with self.session_factory() as session:
            result = await session.execute(
                select(ContactModel).where(
                    ContactModel.user_id == user_id,
                    ContactModel.account_number == account_number,
                ),
            )
            return result.scalar_one_or_none()
