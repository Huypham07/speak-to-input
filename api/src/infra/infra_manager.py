from __future__ import annotations

from typing import Optional

from domain.plugins.registry import initialize_plugins
from infra.db import PostgresConnection
from infra.db.repositories import AccountRepository
from infra.db.repositories import BillRepository
from infra.db.repositories import ContactRepository
from infra.db.repositories import SavingsFundRepository
from infra.db.repositories import SessionRepository
from infra.db.repositories import TransactionRepository
from infra.db.repositories import UserRepository
from shared.logging import get_logger
from shared.settings import Settings

logger = get_logger(__name__)


class InfrastructureManager:
    """
    Manager for infrastructure-level dependencies only.
    Handles: Database, Repositories, External APIs.

    Services are created at API layer to avoid circular imports.
    """

    def __init__(self, settings: Settings):
        self.settings = settings

        # Infrastructure
        self._postgres: Optional[PostgresConnection] = None

        # Repositories
        self._session_repository: Optional[SessionRepository] = None
        self._user_repository: Optional[UserRepository] = None
        self._account_repository: Optional[AccountRepository] = None
        self._contact_repository: Optional[ContactRepository] = None
        self._transaction_repository: Optional[TransactionRepository] = None
        self._bill_repository: Optional[BillRepository] = None
        self._fund_repository: Optional[SavingsFundRepository] = None

    async def initialize(self) -> None:
        """Initialize all infrastructure connections and services"""
        try:
            # Initialize database
            self._postgres = PostgresConnection(self.settings)
            await self._postgres.connect()
            logger.info('PostgreSQL connection established')

            await self._postgres.init_models()
            logger.info('Database models initialized')

            # Initialize repositories
            self._initialize_repositories()
            logger.info('Repositories initialized')

            # Initialize plugins
            initialize_plugins()
            logger.info('Intent plugins initialized')

            logger.info('Infrastructure initialized successfully')

        except Exception as e:
            logger.error(f'Failed to initialize infrastructure: {e}')
            raise

    def _initialize_repositories(self) -> None:
        """Initialize all repositories"""
        if not self._postgres:
            raise RuntimeError('PostgreSQL connection is not initialized')
        session_factory = self._postgres.get_session

        self._session_repository = SessionRepository(session_factory)
        self._user_repository = UserRepository(session_factory)
        self._account_repository = AccountRepository(session_factory)
        self._contact_repository = ContactRepository(session_factory)
        self._transaction_repository = TransactionRepository(session_factory)
        self._bill_repository = BillRepository(session_factory)
        self._fund_repository = SavingsFundRepository(session_factory)

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
    def postgres(self) -> PostgresConnection:
        """Get PostgreSQL connection"""
        if not self._postgres:
            raise RuntimeError('PostgreSQL not initialized')
        return self._postgres

    # Repositories
    @property
    def session_repository(self) -> SessionRepository:
        """Get Session repository"""
        if not self._session_repository:
            raise RuntimeError('SessionRepository not initialized')
        return self._session_repository

    @property
    def user_repository(self) -> UserRepository:
        """Get User repository"""
        if not self._user_repository:
            raise RuntimeError('UserRepository not initialized')
        return self._user_repository

    @property
    def account_repository(self) -> AccountRepository:
        """Get Account repository"""
        if not self._account_repository:
            raise RuntimeError('AccountRepository not initialized')
        return self._account_repository

    @property
    def contact_repository(self) -> ContactRepository:
        """Get Contact repository"""
        if not self._contact_repository:
            raise RuntimeError('ContactRepository not initialized')
        return self._contact_repository

    @property
    def transaction_repository(self) -> TransactionRepository:
        """Get Transaction repository"""
        if not self._transaction_repository:
            raise RuntimeError('TransactionRepository not initialized')
        return self._transaction_repository

    @property
    def bill_repository(self) -> BillRepository:
        """Get Bill repository"""
        if not self._bill_repository:
            raise RuntimeError('BillRepository not initialized')
        return self._bill_repository

    @property
    def fund_repository(self) -> SavingsFundRepository:
        """Get Savings Fund repository"""
        if not self._fund_repository:
            raise RuntimeError('SavingsFundRepository not initialized')
        return self._fund_repository
