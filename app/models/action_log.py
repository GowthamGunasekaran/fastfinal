"""
SQLAlchemy ORM model for the `action_log` table.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.utils.helpers import generate_uuid, utcnow


class ActionLog(Base):
    __tablename__ = "action_log"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    pager_id: Mapped[Optional[str]] = mapped_column(
        String(36), nullable=True, index=True
    )
    user_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    role: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    market: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    date_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now(), nullable=True
    )
    action: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
