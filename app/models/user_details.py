"""
SQLAlchemy ORM model for the `user_details` table.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.utils.helpers import utcnow


class UserDetails(Base):
    __tablename__ = "user_details"

    email: Mapped[str] = mapped_column(
        String(255), primary_key=True
    )
    role: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    market: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now(), nullable=True
    )
    last_updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, server_default=func.now(), nullable=True
    )
