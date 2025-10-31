from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import Integer
from sqlalchemy import JSON
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from .base_orm import BaseModel


class SessionModel(BaseModel):
    """
    Model for storing conversation sessions.
    Persists session state across requests.
    """

    __tablename__ = 'sessions'

    # Primary fields
    session_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        index=True,
        nullable=True,
    )

    # State tracking
    current_state: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default='IDLE',
    )
    previous_state: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )

    # Intent tracking
    current_intent: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    intent_confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )

    # Data storage
    context: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    parameters: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    # Metadata
    turn_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Flags
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    requires_confirmation: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    def __repr__(self) -> str:
        return f'<Session {self.session_id} state={self.current_state} intent={self.current_intent}>'
