"""
Campaign service — business logic for Campaign endpoints.
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from app.db.models.campaign import Campaign
from app.repositories.campaign_repository import campaign_repository
from app.schemas.campaign_schema import CampaignCreate, CampaignOut, CampaignListResponse


class CampaignService:

    def create_campaign(self, db: Session, payload: CampaignCreate) -> CampaignOut:
        campaign = Campaign(
            market=payload.market,
            campaign_name=payload.campaign_name,
            created_by=payload.created_by or payload.user_id,
        )
        saved = campaign_repository.create(db, campaign)
        db.commit()
        db.refresh(saved)
        return CampaignOut.model_validate(saved)

    def list_campaigns(
        self,
        db: Session,
        market: Optional[List[str]] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> CampaignListResponse:
        campaigns = campaign_repository.list_all(
            db, market=market, skip=skip, limit=limit
        )
        total = campaign_repository.count(db, market=market)
        return CampaignListResponse(
            total=total,
            campaigns=[CampaignOut.model_validate(c) for c in campaigns],
        )


campaign_service = CampaignService()
