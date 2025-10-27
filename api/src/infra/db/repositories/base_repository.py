from __future__ import annotations

from typing import Callable
from typing import Type
from typing import TypeVar

from domain.entities import BaseModel
from shared.exceptions import DuplicatedError
from shared.exceptions import NotFoundError
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar('T', bound=BaseModel)


class BaseRepository:
    def __init__(self, session_factory: Callable[[], AsyncSession], model: Type[T]) -> None:
        self.session_factory = session_factory
        self.model = model

    async def read_by_id(self, id: int):
        async with self.session_factory() as session:
            result = await session.get(self.model, id)
            return result

    async def create(self, schema: T):
        async with self.session_factory() as session:
            query = self.model(**schema.dict())
            session.add(query)
            try:
                await session.commit()
                await session.refresh(query)
                return query
            except IntegrityError as e:
                await session.rollback()
                raise DuplicatedError(detail=str(e)) from e

    async def update(self, id: int, schema: T):
        async with self.session_factory() as session:
            await session.execute(
                update(self.model).where(self.model.id == id).values(**schema.dict(exclude_none=True)),
            )
            await session.commit()
            return await self.read_by_id(id)

    async def delete_by_id(self, id: int):
        async with self.session_factory() as session:
            query = await session.get(self.model, id)
            if not query:
                raise NotFoundError(detail=f'not found id : {id}')
            await session.delete(query)
            await session.commit()
