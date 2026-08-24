"""
SQLAlchemy ORM model for the `pager` table.
"""

from datetime import datetime
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import String, DateTime, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.utils.enums import ScoringMode, PagerStatus
from app.utils.helpers import generate_uuid, utcnow

if TYPE_CHECKING:
    from app.models.pillar import Pillar


class Pager(Base):
    __tablename__ = "pager"

    pager_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)

    # Metadata dimensions
    market: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    retailer: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    channel: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    campaign_focus: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    business_outcome_statement: Mapped[Optional[str]] = mapped_column(
        String(1000), nullable=True
    )

    scoring_mode: Mapped[ScoringMode] = mapped_column(
        SAEnum(ScoringMode, native_enum=False),
        nullable=False,
        default=ScoringMode.UNWEIGHTED,
    )

    status: Mapped[PagerStatus] = mapped_column(
        SAEnum(PagerStatus, native_enum=False),
        nullable=False,
        default=PagerStatus.DRAFT,
    )

    track: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    pager_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    # Audit fields
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=True
    )
    updated_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=True
    )
    published_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    pillars: Mapped[List["Pillar"]] = relationship(
        "Pillar",
        back_populates="pager",
        cascade="all, delete-orphan",
        order_by="Pillar.pillar_number",
    )
