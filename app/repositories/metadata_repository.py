"""
Repository for Metadata database operations.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, distinct

from app.db.models.metadata import Metadata


class MetadataRepository:

    def create(self, db: Session, metadata: Metadata) -> Metadata:
        db.add(metadata)
        db.flush()
        return metadata

    def create_many(self, db: Session, records: List[Metadata]) -> None:
        db.add_all(records)
        db.flush()

    def get_by_id(self, db: Session, metadata_id: int) -> Optional[Metadata]:
        return db.get(Metadata, metadata_id)

    def list_all(self, db: Session) -> List[Metadata]:
        return list(db.scalars(select(Metadata)).all())

    def get_filtered_values(
        self,
        db: Session,
        market: Optional[List[str]] = None,
        region: Optional[List[str]] = None,
        channel: Optional[List[str]] = None,
        category: Optional[List[str]] = None,
        campaign: Optional[List[str]] = None,
    ) -> dict:
        """
        Return distinct values for each dimension based on IN-filter semantics.
        Empty list = no filter for that field.
        """

        def _build_stmt(column, filters: dict):
            stmt = select(distinct(column))
            for field, values in filters.items():
                if values:
                    col = getattr(Metadata, field)
                    stmt = stmt.where(col.in_(values))
            return stmt

        active_filters = {
            "market": market or [],
            "region": region or [],
            "channel": channel or [],
            "category": category or [],
            "campaign": campaign or [],
        }

        def _fetch(column_name: str) -> List[str]:
            col = getattr(Metadata, column_name)
            stmt = _build_stmt(col, active_filters)
            return sorted(db.scalars(stmt).all())

        return {
            "market": _fetch("market"),
            "region": _fetch("region"),
            "channel": _fetch("channel"),
            "category": _fetch("category"),
            "campaign": _fetch("campaign"),
        }

    def count(self, db: Session) -> int:
        from sqlalchemy import func
        return db.scalar(select(func.count()).select_from(Metadata)) or 0


metadata_repository = MetadataRepository()
