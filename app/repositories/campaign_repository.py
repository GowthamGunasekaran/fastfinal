"""
Repository for Campaign database operations.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, distinct

from app.db.models.campaign import Campaign


class CampaignRepository:

    def create(self, db: Session, campaign: Campaign) -> Campaign:
        db.add(campaign)
        db.flush()
        return campaign

    def get_by_id(self, db: Session, campaign_id: str) -> Optional[Campaign]:
        return db.get(Campaign, campaign_id)

    def list_all(
        self,
        db: Session,
        market: Optional[List[str]] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Campaign]:
        stmt = select(Campaign)
        if market:
            flattened_markets = []
            for m in market:
                if m:
                    flattened_markets.extend([x.strip() for x in m.split(",") if x.strip()])
            if flattened_markets:
                stmt = stmt.where(Campaign.market.in_(flattened_markets))
        stmt = stmt.offset(skip).limit(limit)
        return list(db.scalars(stmt).all())

    def get_distinct_campaign_names(
        self, db: Session, market: Optional[List[str]] = None
    ) -> List[str]:
        stmt = select(distinct(Campaign.campaign_name))
        if market:
            flattened_markets = []
            for m in market:
                if m:
                    flattened_markets.extend([x.strip() for x in m.split(",") if x.strip()])
            if flattened_markets:
                stmt = stmt.where(Campaign.market.in_(flattened_markets))
        return sorted(db.scalars(stmt).all())

    def get_campaign_names_by_market(
        self, db: Session, market: Optional[List[str]] = None
    ) -> dict:
        stmt = select(Campaign.market, Campaign.campaign_name).distinct()
        if market:
            flattened_markets = []
            for m in market:
                if m:
                    flattened_markets.extend([x.strip() for x in m.split(",") if x.strip()])
            if flattened_markets:
                stmt = stmt.where(Campaign.market.in_(flattened_markets))
        rows = db.execute(stmt).all()
        result: dict = {}
        for m_name, c_name in rows:
            if m_name not in result:
                result[m_name] = []
            result[m_name].append(c_name)
        for m_name in result:
            result[m_name] = sorted(result[m_name])
        return result

    def count(self, db: Session, market: Optional[List[str]] = None) -> int:
        from sqlalchemy import func
        stmt = select(func.count()).select_from(Campaign)
        if market:
            flattened_markets = []
            for m in market:
                if m:
                    flattened_markets.extend([x.strip() for x in m.split(",") if x.strip()])
            if flattened_markets:
                stmt = stmt.where(Campaign.market.in_(flattened_markets))
        return db.scalar(stmt) or 0


campaign_repository = CampaignRepository()
