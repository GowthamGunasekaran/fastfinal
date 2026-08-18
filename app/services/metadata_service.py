from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from app.repositories.metadata_repository import metadata_repository
from app.repositories.campaign_repository import campaign_repository
from app.schemas.metadata_schema import (
    MarketMetadataItem,
    MetadataFilterRequest,
)


class MetadataService:

    def get_cascading_filters(
        self, db: Session, request: Optional[MetadataFilterRequest] = None
    ) -> Dict[str, MarketMetadataItem]:
        """
        Returns a dictionary keyed by market name.
        Each market object contains arrays of strings for retailer, channel, category, and campaign.
        If request.market is provided, filters for those markets only; otherwise returns all.
        """
        market_filters = request.market if request and request.market else None
        meta_records = metadata_repository.get_by_markets(db, markets=market_filters)
        campaigns_by_market = campaign_repository.get_campaign_names_by_market(
            db, market=market_filters
        )

        response: Dict[str, MarketMetadataItem] = {}

        # Populate from metadata records
        for meta in meta_records:
            m_name = meta.market
            retailer_list = meta.retailer if isinstance(meta.retailer, list) else []
            channel_list = meta.channel if isinstance(meta.channel, list) else []
            category_list = meta.category if isinstance(meta.category, list) else []
            campaign_list = campaigns_by_market.get(m_name, [])

            response[m_name] = MarketMetadataItem(
                retailer=retailer_list,
                channel=channel_list,
                category=category_list,
                campaign=campaign_list,
            )

        # Include any markets that might only be in campaigns table if not already populated
        for c_market, c_list in campaigns_by_market.items():
            if c_market not in response:
                response[c_market] = MarketMetadataItem(
                    retailer=[],
                    channel=[],
                    category=[],
                    campaign=c_list,
                )

        return response


metadata_service = MetadataService()
