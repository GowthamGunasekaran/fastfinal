"""
SQLAlchemy ORM model for the `pillar` table.
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import String, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.utils.helpers import generate_uuid, utcnow


class Pillar(Base):
    __tablename__ = "pillar"

    pillar_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    pager_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("pager.pager_id", ondelete="CASCADE"), nullable=False
    )

    pillar_number: Mapped[int] = mapped_column(Integer, nullable=False)
    pillar_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    pillar_description: Mapped[Optional[str]] = mapped_column(
        String(1000), nullable=True
    )
    pillar_weight: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pillar_track: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=True
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=True
    )

    # Relationships
    pager: Mapped["Pager"] = relationship("Pager", back_populates="pillars")
    initiatives: Mapped[List["PillarInitiative"]] = relationship(
        "PillarInitiative",
        back_populates="pillar",
        cascade="all, delete-orphan",
        order_by="PillarInitiative.initiative_number",
    )
