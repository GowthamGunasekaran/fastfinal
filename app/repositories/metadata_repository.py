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

    def get_by_market(self, db: Session, market: str) -> Optional[Metadata]:
        return db.scalar(select(Metadata).where(Metadata.market == market))

    def get_by_markets(
        self, db: Session, markets: Optional[List[str]] = None
    ) -> List[Metadata]:
        stmt = select(Metadata)
        if markets:
            flattened_markets = []
            for m in markets:
                if m:
                    flattened_markets.extend([x.strip() for x in m.split(",") if x.strip()])
            if flattened_markets:
                stmt = stmt.where(Metadata.market.in_(flattened_markets))
        return list(db.scalars(stmt).all())

    def list_all(self, db: Session) -> List[Metadata]:
        return list(db.scalars(select(Metadata)).all())

    def upsert(
        self,
        db: Session,
        market: str,
        retailer: List[str],
        channel: List[str],
        category: List[str],
    ) -> Metadata:
        existing = self.get_by_market(db, market)
        if existing:
            existing.retailer = retailer
            existing.channel = channel
            existing.category = category
            db.flush()
            return existing
        else:
            meta = Metadata(
                market=market,
                retailer=retailer,
                channel=channel,
                category=category,
            )
            db.add(meta)
            db.flush()
            return meta

    def count(self, db: Session) -> int:
        from sqlalchemy import func
        return db.scalar(select(func.count()).select_from(Metadata)) or 0


metadata_repository = MetadataRepository()
