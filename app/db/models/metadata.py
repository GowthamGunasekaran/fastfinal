from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Metadata(Base):
    __tablename__ = "metadata"

    metadata_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    market: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    retailer: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    campaign: Mapped[str] = mapped_column(String(150), nullable=False, index=True)