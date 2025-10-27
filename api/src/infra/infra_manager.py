from __future__ import annotations

from typing import Optional

from infra.db import PostgresConnection
from shared.logging import get_logger
from shared.settings import Settings

logger = get_logger(__name__)


class InfrastructureManager:
    """Manager for all infrastructure connections"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._postgres: Optional[PostgresConnection] = None

    async def initialize(self) -> None:
        """Initialize all infrastructure connections"""
        try:
            # Initialize Athena PostgreSQL
            self._postgres = PostgresConnection(self.settings)
            await self._postgres.connect()

            logger.info('Infrastructure initialized successfully')

        except Exception as e:
            logger.error(f'Failed to initialize infrastructure: {e}')
            raise

    async def cleanup(self) -> None:
        """Cleanup all connections"""
        try:
            if self._postgres:
                await self._postgres.close()
                logger.info('PostgreSQL connection closed')

            logger.info('Infrastructure cleanup completed')

        except Exception as e:
            logger.error(f'Error during infrastructure cleanup: {e}')

    # Property accessors
    @property
    def postgres(self) -> Optional[PostgresConnection]:
        """Get PostgreSQL connection"""
        return self._postgres
