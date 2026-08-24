"""
SQLAlchemy ORM model for the `pillar_initiative` table.

image_urls is stored as JSON (list of strings) directly on this table.
No separate image table is used.
"""

from datetime import datetime
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import String, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.utils.helpers import generate_uuid, utcnow

if TYPE_CHECKING:
    from app.models.pillar import Pillar


class PillarInitiative(Base):
    __tablename__ = "pillar_initiative"

    # Integer primary key — auto-increment
    pillar_initiative_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )

    # UUID string — unique business identifier for the initiative
    initiative_id: Mapped[str] = mapped_column(
        String(36), unique=True, nullable=False, default=generate_uuid
    )

    pager_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("pager.pager_id", ondelete="CASCADE"), nullable=False
    )
    pillar_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("pillar.pillar_id", ondelete="CASCADE"), nullable=False
    )

    initiative_number: Mapped[int] = mapped_column(Integer, nullable=False)
    initiative_track: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    priority_level: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    accountable_function_department: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    initiative_description: Mapped[Optional[str]] = mapped_column(
        String(2000), nullable=True
    )
    kpi_metric: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    success_target: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    unit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    week_start: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    week_end: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    guidelines: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    checklist_compliance_notes: Mapped[Optional[str]] = mapped_column(
        String(2000), nullable=True
    )

    # JSON column — list of image URL strings (max 3)
    image_urls: Mapped[Optional[List[str]]] = mapped_column(
        JSON, nullable=True, default=list
    )

    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=True
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=True
    )

    # Relationships
    pillar: Mapped["Pillar"] = relationship("Pillar", back_populates="initiatives")
