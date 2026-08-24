"""
SQLAlchemy ORM model for the `metadata` table.

Each row represents one valid combination of metadata dimensions.
The frontend uses this table for cascading dropdown filters.
"""

from typing import List
from sqlalchemy import Integer, String, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Metadata(Base):
    __tablename__ = "metadata"

    metadata_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    market: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    retailer: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    channel: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    category: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    accountable_team: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    pillar_kpi_1: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    pillar_kpi_2: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    pillar_kpi_3: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    pillar_kpi_4: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    pillar_kpi_5: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
