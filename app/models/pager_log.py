"""
SQLAlchemy ORM model for the `pager_log` table.

Tracks every user action performed on a Pager (create, edit, status change, etc.)
for full audit-trail visibility.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.utils.helpers import utcnow


class PagerLog(Base):
    __tablename__ = "pager_log"

    pager_log_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )

    pager_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    # Who performed the action
    created_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_by_role: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_updated_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)

    # Timestamps
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=True
    )
    last_modified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=True
    )

    # Action label: CREATE | EDIT | PUBLISH | ARCHIVE | DELETE | STATUS_UPDATE
    action: Mapped[str] = mapped_column(String(50), nullable=False)

    # Full JSON payload that triggered this action
    payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
