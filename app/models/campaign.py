"""
SQLAlchemy ORM model for the `campaign` table.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.utils.helpers import generate_uuid, utcnow


class Campaign(Base):
    __tablename__ = "campaign"

    campaign_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    market: Mapped[str] = mapped_column(String(100), nullable=False)
    campaign_name: Mapped[str] = mapped_column(String(200), nullable=False)
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=utcnow
    )
