"""
Landing page service — fetches only PUBLISHED pagers with multi-select filters.
"""

from sqlalchemy.orm import Session

from app.repositories.pager_repository import pager_repository
from app.schemas.landing_page_schema import LandingPageFilterRequest, LandingPageResponse


class LandingPageService:

    def get_published_pagers(
        self,
        db: Session,
        filters: LandingPageFilterRequest,
        skip: int = 0,
        limit: int = 100,
    ) -> LandingPageResponse:
        pagers = pager_repository.list_published(
            db,
            market=filters.market or [],
            region=filters.region or [],
            channel=filters.channel or [],
            category=filters.category or [],
            campaign_focus=filters.campaign_focus or [],
            pager_type=filters.pager_type or [],
            skip=skip,
            limit=limit,
        )
        return LandingPageResponse(total=len(pagers), pagers=pagers)


landing_page_service = LandingPageService()
