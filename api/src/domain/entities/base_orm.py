from __future__ import annotations

from datetime import datetime

from pydantic import Field
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import func
from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase


class BaseModel(DeclarativeBase):
    metadata = MetaData(
        naming_convention={
            'ix': '%(table_name)s_%(column_0_label)s_idx',
            'uq': 'uq_%(table_name)s_%(column_0_name)s',
            'ck': 'ck_%(table_name)s_%(constraint_name)s',
            'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
            'pk': 'pk_%(table_name)s',
        },
    )

    id: int = Field(primary_key=True)
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), default=func.now()))
    updated_at: datetime = Field(sa_column=Column(DateTime(timezone=True), default=func.now(), onupdate=func.now()))
