"""
SQLAlchemy ORM model for the `metadata` table.

Each row represents one valid combination of metadata dimensions.
The frontend uses this table for cascading dropdown filters.
"""

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Metadata(Base):
    __tablename__ = "metadata"

    metadata_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    market: Mapped[str] = mapped_column(String(100), nullable=False)
    region: Mapped[str] = mapped_column(String(100), nullable=False)
    channel: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    campaign: Mapped[str] = mapped_column(String(100), nullable=False)
