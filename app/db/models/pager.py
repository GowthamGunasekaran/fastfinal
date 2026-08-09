from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Pager(Base):
    __tablename__ = "pager"

    pager_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    market: Mapped[str | None] = mapped_column(String(100))
    category: Mapped[str | None] = mapped_column(String(100))
    campaign_focus: Mapped[str | None] = mapped_column(String(200))
    channel: Mapped[str | None] = mapped_column(String(100))
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    business_outcome_statement: Mapped[str | None] = mapped_column(Text)

    scoring_mode: Mapped[str] = mapped_column(String(20), nullable=False)
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

    pillars: Mapped[list["PagerPillarInitiative"]] = relationship(
        "PagerPillarInitiative",
        back_populates="pager",
        cascade="all, delete-orphan",
        order_by="PagerPillarInitiative.pillar_number, PagerPillarInitiative.initiative_number",
    )
