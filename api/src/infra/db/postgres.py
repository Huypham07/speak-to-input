from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from shared.logging import get_logger
from shared.settings import Settings
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine

from .base_connection import BaseDBConnection
from .models import BaseModel

logger = get_logger(__name__)


class PostgresConnection(BaseDBConnection):
    """PostgreSQL connection"""

    def __init__(self, settings: Settings):
        super().__init__(settings)
        self._session_factory = None

    async def connect(self) -> None:
        """Connect to PostgreSQL"""
        try:
            self._client = create_async_engine(
                self.settings.postgres.connection_url,
                echo=False,
                pool_size=self.settings.postgres.pool_size,
                max_overflow=0,
                pool_pre_ping=True,
                pool_recycle=3600,
            )

            self._session_factory = async_sessionmaker(
                bind=self._client,
                class_=AsyncSession,
                expire_on_commit=False,
            )

            logger.info('PostgreSQL connected successfully')

        except Exception as e:
            logger.error(f'Failed to connect to PostgreSQL: {e}')
            raise

    async def init_models(self):
        async with self._client.begin() as conn:
            await conn.run_sync(BaseModel.metadata.create_all)

    async def close(self) -> None:
        """Close PostgreSQL connection"""
        if self._client:
            await self._client.dispose()
            self._client = None
            self._session_factory = None
            logger.info('PostgreSQL connection closed')

    @property
    def engine(self):
        """Get SQLAlchemy engine"""
        return self.client

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session"""
        if not self._session_factory:
            raise RuntimeError('PostgreSQL not connected. Call connect() first.')

        session = self._session_factory()
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
