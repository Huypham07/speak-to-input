from __future__ import annotations

from abc import ABC
from abc import abstractmethod

from shared.settings import Settings


class BaseDBConnection(ABC):
    """Base class for all database connections"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._client = None

    @abstractmethod
    async def connect(self) -> None:
        """Connect to database"""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close database connection"""
        pass

    @property
    def client(self):
        """Get database client/engine"""
        if not self._client:
            raise RuntimeError(f'{self.__class__.__name__} not connected. Call connect() first.')
        return self._client

    @property
    def is_connected(self) -> bool:
        """Check if connected"""
        return self._client is not None
