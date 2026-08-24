"""
Repository for Metadata database operations.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, distinct

from app.models.metadata import Metadata


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
        accountable_team: Optional[List[str]] = None,
        pillar_kpi_1: Optional[List[str]] = None,
        pillar_kpi_2: Optional[List[str]] = None,
        pillar_kpi_3: Optional[List[str]] = None,
        pillar_kpi_4: Optional[List[str]] = None,
        pillar_kpi_5: Optional[List[str]] = None,
    ) -> Metadata:
        acc_team = accountable_team if accountable_team is not None else []
        pk1 = pillar_kpi_1 if pillar_kpi_1 is not None else []
        pk2 = pillar_kpi_2 if pillar_kpi_2 is not None else []
        pk3 = pillar_kpi_3 if pillar_kpi_3 is not None else []
        pk4 = pillar_kpi_4 if pillar_kpi_4 is not None else []
        pk5 = pillar_kpi_5 if pillar_kpi_5 is not None else []

        existing = self.get_by_market(db, market)
        if existing:
            existing.retailer = retailer
            existing.channel = channel
            existing.category = category
            existing.accountable_team = acc_team
            existing.pillar_kpi_1 = pk1
            existing.pillar_kpi_2 = pk2
            existing.pillar_kpi_3 = pk3
            existing.pillar_kpi_4 = pk4
            existing.pillar_kpi_5 = pk5
            db.flush()
            return existing
        else:
            meta = Metadata(
                market=market,
                retailer=retailer,
                channel=channel,
                category=category,
                accountable_team=acc_team,
                pillar_kpi_1=pk1,
                pillar_kpi_2=pk2,
                pillar_kpi_3=pk3,
                pillar_kpi_4=pk4,
                pillar_kpi_5=pk5,
            )
            db.add(meta)
            db.flush()
            return meta

    def count(self, db: Session) -> int:
        from sqlalchemy import func
        return db.scalar(select(func.count()).select_from(Metadata)) or 0


metadata_repository = MetadataRepository()
