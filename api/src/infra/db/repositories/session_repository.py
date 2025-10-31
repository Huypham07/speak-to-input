from __future__ import annotations

from datetime import datetime
from typing import Callable
from typing import Optional

from domain.entities.session import Session
from domain.value_objects import IntentType
from domain.value_objects import StateType
from infra.db.models.session_model import SessionModel
from shared.exceptions import NotFoundError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .base_repository import BaseRepository


class SessionRepository(BaseRepository):
    """Repository for managing session persistence"""

    def __init__(self, session_factory: Callable[[], AsyncSession]):
        super().__init__(session_factory, SessionModel)

    async def get_by_session_id(self, session_id: str) -> Optional[SessionModel]:
        """Get session by ID"""
        async with self.session_factory() as db_session:
            result = await db_session.execute(
                select(SessionModel).where(SessionModel.session_id == session_id),
            )
            return result.scalar_one_or_none()

    async def get_or_create(self, session_id: str, user_id: Optional[str] = None) -> SessionModel:
        """Get existing session or create new one"""
        session = await self.get_by_session_id(session_id)

        if session is None:
            session = Session(
                session_id=session_id,
                user_id=user_id,
                current_state=StateType.IDLE,
            )
            await self.save(session)

        return session

    async def save(self, session: Session) -> SessionModel:
        """Save or update session"""
        async with self.session_factory() as db_session:
            # Check if exists
            result = await db_session.execute(
                select(SessionModel).where(SessionModel.session_id == session.session_id),
            )
            existing = result.scalar_one_or_none()

            if existing:
                # Update
                for field, value in session.model_dump().items():
                    setattr(existing, field, value)
            else:
                # Create
                db_session.add(SessionModel(**session.model_dump()))

            await db_session.commit()

            if existing:
                await db_session.refresh(existing)
                return existing
            else:
                # Refresh the newly created model
                result = await db_session.execute(
                    select(SessionModel).where(SessionModel.session_id == session.session_id),
                )
                return result.scalar_one()

    async def delete_expired(self) -> int:
        """Delete all expired sessions"""
        async with self.session_factory() as db_session:
            now = datetime.now()
            result = await db_session.execute(
                select(SessionModel).where(
                    SessionModel.expires_at.isnot(None),
                    SessionModel.expires_at < now,
                ),
            )
            models = result.scalars().all()
            count = len(models)

            for model in models:
                await db_session.delete(model)

            await db_session.commit()
            return count
