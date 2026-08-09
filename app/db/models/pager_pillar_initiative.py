from datetime import date, datetime

from sqlalchemy import JSON, Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class PagerPillarInitiative(Base):
    __tablename__ = "pager_pillar_initiative"

    pillar_initiative_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )

    pager_id: Mapped[int] = mapped_column(
        ForeignKey("pager.pager_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    pillar_id: Mapped[str] = mapped_column(String(36), nullable=False)
    pillar_number: Mapped[int] = mapped_column(Integer, nullable=False)
    pillar_name: Mapped[str | None] = mapped_column(String(200))
    pillar_description: Mapped[str | None] = mapped_column(Text)
    pillar_weight: Mapped[float | None] = mapped_column(nullable=True)

    initiative_id: Mapped[str] = mapped_column(String(36), nullable=False)
    initiative_number: Mapped[int] = mapped_column(Integer, nullable=False)

    priority_level: Mapped[str | None] = mapped_column(String(20))
    accountable_function_department: Mapped[str | None] = mapped_column(String(200))
    initiative_description: Mapped[str | None] = mapped_column(Text)
    kpi_metric: Mapped[str | None] = mapped_column(String(200))
    success_target: Mapped[str | None] = mapped_column(String(100))
    unit: Mapped[str | None] = mapped_column(String(50))
    week_start: Mapped[date | None] = mapped_column(Date)
    week_end: Mapped[date | None] = mapped_column(Date)
    guidelines: Mapped[str | None] = mapped_column(Text)
    checklist_compliance_notes: Mapped[str | None] = mapped_column(Text)

    # Python list[str] <-> JSON array in SQLite.
    image_urls: Mapped[list[str]] = mapped_column(
        JSON, default=list, nullable=False
    )

    status: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), nullable=False
    )
    created_by: Mapped[str] = mapped_column(String(100), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        nullable=False,
    )
    updated_by: Mapped[str] = mapped_column(String(100), nullable=False)

    pager: Mapped["Pager"] = relationship(
        "Pager",
        back_populates="pillars",
    )
