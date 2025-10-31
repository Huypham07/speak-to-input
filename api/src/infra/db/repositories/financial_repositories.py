from __future__ import annotations

from datetime import datetime
from datetime import timedelta
from decimal import Decimal
from typing import Any
from typing import Callable
from typing import Dict
from typing import Optional

from domain.entities.transaction import Bill
from infra.db.models.financial_models import BillModel
from infra.db.models.financial_models import FundTransactionModel
from infra.db.models.financial_models import SavingsFundModel
from infra.db.models.financial_models import TransactionModel
from shared.exceptions import NotFoundError
from sqlalchemy import select
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from .base_repository import BaseRepository


class TransactionRepository(BaseRepository):
    """Repository for Transaction management"""

    def __init__(self, session_factory: Callable[[], AsyncSession]):
        super().__init__(session_factory, TransactionModel)

    async def get_by_user_id(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> list[TransactionModel]:
        """Get transactions for a user"""
        async with self.session_factory() as session:
            result = await session.execute(
                select(TransactionModel)
                .where(TransactionModel.user_id == user_id)
                .order_by(TransactionModel.created_at.desc())
                .limit(limit)
                .offset(offset),
            )
            return result.scalars().all()

    async def get_by_account_id(
        self,
        account_id: int,
        limit: int = 50,
    ) -> list[TransactionModel]:
        """Get transactions for an account"""
        async with self.session_factory() as session:
            result = await session.execute(
                select(TransactionModel)
                .where(
                    (TransactionModel.from_account_id == account_id) |
                    (TransactionModel.to_account_id == account_id),
                )
                .order_by(TransactionModel.created_at.desc())
                .limit(limit),
            )
            return result.scalars().all()

    async def update_status(
        self,
        transaction_id: int,
        status: str,
    ) -> TransactionModel:
        """Update transaction status"""
        async with self.session_factory() as session:
            values: Dict[str, Any] = {'status': status}

            # If completing, set completed_at
            if status == 'completed':
                values['completed_at'] = datetime.now()

            await session.execute(
                update(TransactionModel)
                .where(TransactionModel.id == transaction_id)
                .values(**values),
            )
            await session.commit()

            # Return updated transaction
            result = await session.execute(
                select(TransactionModel).where(TransactionModel.id == transaction_id),
            )
            model = result.scalar_one_or_none()

            if not model:
                raise NotFoundError(detail=f'Transaction {transaction_id} not found')

            return model


class BillRepository(BaseRepository):
    """Repository for Bill management"""

    def __init__(self, session_factory: Callable[[], AsyncSession]):
        super().__init__(session_factory, BillModel)

    async def get_by_user_id(
        self,
        user_id: int,
        status: Optional[str] = None,
    ) -> list[BillModel]:
        """Get bills for a user, optionally filtered by status"""
        async with self.session_factory() as session:
            query = select(BillModel).where(BillModel.user_id == user_id)

            if status:
                query = query.where(BillModel.status == status)

            query = query.order_by(BillModel.due_date.asc())

            result = await session.execute(query)
            return result.scalars().all()

    async def get_upcoming(
        self,
        user_id: int,
        days: int = 7,
    ) -> list[BillModel]:
        """Get upcoming bills within X days"""
        async with self.session_factory() as session:
            from_date = datetime.now()
            to_date = from_date + timedelta(days=days)

            result = await session.execute(
                select(BillModel)
                .where(
                    BillModel.user_id == user_id,
                    BillModel.status == 'pending',
                    BillModel.due_date.between(from_date, to_date),
                )
                .order_by(BillModel.due_date.asc()),
            )
            return result.scalars().all()

    async def mark_as_paid(self, bill_id: int) -> Bill:
        """Mark bill as paid"""
        async with self.session_factory() as session:
            await session.execute(
                update(BillModel)
                .where(BillModel.id == bill_id)
                .values(
                    status='paid',
                    paid_at=datetime.now(),
                ),
            )
            await session.commit()

            # Return updated bill
            result = await session.execute(
                select(BillModel).where(BillModel.id == bill_id),
            )
            model = result.scalar_one_or_none()

            if not model:
                raise NotFoundError(detail=f'Bill {bill_id} not found')

            return model


class SavingsFundRepository(BaseRepository):
    """Repository for Savings Fund management"""

    def __init__(self, session_factory: Callable[[], AsyncSession]):
        super().__init__(session_factory, SavingsFundModel)

    async def get_by_user_id(
        self,
        user_id: int,
        status: Optional[str] = None,
    ) -> list[SavingsFundModel]:
        """Get funds for a user, optionally filtered by status"""
        async with self.session_factory() as session:
            query = select(SavingsFundModel).where(SavingsFundModel.user_id == user_id)

            if status:
                query = query.where(SavingsFundModel.status == status)

            query = query.order_by(SavingsFundModel.target_date.asc())

            result = await session.execute(query)
            return result.scalars().all()

    async def deposit(
        self,
        fund_id: int,
        amount: Decimal,
        transaction_id: Optional[int] = None,
    ) -> SavingsFundModel:
        """Deposit money into fund"""
        async with self.session_factory() as session:
            result = await session.execute(
                select(SavingsFundModel).where(SavingsFundModel.id == fund_id),
            )
            model = result.scalar_one_or_none()

            if not model:
                raise NotFoundError(detail=f'Fund {fund_id} not found')

            # Update fund balance
            model.current_amount += amount

            # Check if target reached
            if model.current_amount >= model.target_amount and model.status == 'active':
                model.status = 'completed'
                model.completed_at = datetime.now()

            # Create fund transaction record
            fund_txn = FundTransactionModel(
                fund_id=fund_id,
                transaction_id=transaction_id,
                transaction_type='deposit',
                amount=amount,
            )
            session.add(fund_txn)

            await session.commit()
            await session.refresh(model)

            return model

    async def withdraw(
        self,
        fund_id: int,
        amount: Decimal,
        transaction_id: Optional[int] = None,
    ) -> SavingsFundModel:
        """Withdraw money from fund"""
        async with self.session_factory() as session:
            result = await session.execute(
                select(SavingsFundModel).where(SavingsFundModel.id == fund_id),
            )
            model = result.scalar_one_or_none()

            if not model:
                raise NotFoundError(detail=f'Fund {fund_id} not found')

            if model.current_amount < amount:
                raise ValueError('Insufficient fund balance')

            # Update fund balance
            model.current_amount -= amount

            # Create fund transaction record
            fund_txn = FundTransactionModel(
                fund_id=fund_id,
                transaction_id=transaction_id,
                transaction_type='withdrawal',
                amount=amount,
            )
            session.add(fund_txn)

            await session.commit()
            await session.refresh(model)

            return model
