"""
Metadata service — business logic for cascading filter API.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, distinct

from app.db.models.metadata import Metadata
from app.db.models.pager import Pager
from app.repositories.metadata_repository import metadata_repository
from app.repositories.campaign_repository import campaign_repository
from app.schemas.metadata_schema import MetadataFilterRequest, MetadataFilterResponse
from app.utils.enums import PagerStatus


class MetadataService:

    def get_cascading_filters(
        self, db: Session, request: MetadataFilterRequest
    ) -> MetadataFilterResponse:
        """
        Returns distinct values for each metadata dimension
        filtered by the provided multi-select values.
        Campaigns are fetched from the campaign table (filtered by market if provided).
        """
        result = metadata_repository.get_filtered_values(
            db,
            market=request.market or [],
            retailer=request.retailer or [],
            channel=request.channel or [],
            category=request.category or [],
        )

        # Campaigns come from the campaign table (filtered by market if provided)
        campaigns = campaign_repository.get_distinct_campaign_names(
            db, market=request.market or []
        )

        # pager_type and status come from the pager table
        pager_types = self._get_pager_distinct(db, Pager.pager_type, request.pager_type)
        statuses = self._get_pager_distinct(db, Pager.status, request.status)

        return MetadataFilterResponse(
            market=result["market"],
            retailer=result["retailer"],
            channel=result["channel"],
            category=result["category"],
            campaign=campaigns,
            pager_type=pager_types,
            status=statuses,
        )

    def _get_pager_distinct(
        self, db: Session, column, filter_values: Optional[List[str]]
    ) -> List[str]:
        stmt = select(distinct(column)).where(column.isnot(None))
        if filter_values:
            stmt = stmt.where(column.in_(filter_values))
        return sorted(str(v) for v in db.scalars(stmt).all() if v is not None)


metadata_service = MetadataService()
