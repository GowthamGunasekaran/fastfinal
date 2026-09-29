"""
SQLAlchemy ORM model for the `login_log` table.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.utils.helpers import generate_uuid, utcnow


class LoginLog(Base):
    __tablename__ = "login_log"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    user_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    role: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    login_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now(), nullable=True
    )
