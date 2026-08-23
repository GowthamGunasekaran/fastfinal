from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.repositories.metadata_repository import metadata_repository
from app.repositories.campaign_repository import campaign_repository
from app.db.models.campaign import Campaign
from app.utils.helpers import generate_uuid, utcnow
from app.schemas.metadata_schema import (
    MarketMetadataItem,
    MetadataFilterRequest,
    MetadataUpsertRequest,
    MetadataOut,
)


class MetadataService:

    def get_cascading_filters(
        self, db: Session, request: Optional[MetadataFilterRequest] = None
    ) -> Dict[str, MarketMetadataItem]:
        """
        Returns a dictionary keyed by market name.
        Each market object contains arrays of strings for retailer, channel, category, campaign,
        accountable_team, pillar_kpi_1, pillar_kpi_2, pillar_kpi_3, pillar_kpi_4, and pillar_kpi_5.
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
            acc_team_list = meta.accountable_team if isinstance(meta.accountable_team, list) else []
            pk1_list = meta.pillar_kpi_1 if isinstance(meta.pillar_kpi_1, list) else []
            pk2_list = meta.pillar_kpi_2 if isinstance(meta.pillar_kpi_2, list) else []
            pk3_list = meta.pillar_kpi_3 if isinstance(meta.pillar_kpi_3, list) else []
            pk4_list = meta.pillar_kpi_4 if isinstance(meta.pillar_kpi_4, list) else []
            pk5_list = meta.pillar_kpi_5 if isinstance(meta.pillar_kpi_5, list) else []
            campaign_list = campaigns_by_market.get(m_name, [])

            response[m_name] = MarketMetadataItem(
                retailer=retailer_list,
                channel=channel_list,
                category=category_list,
                campaign=campaign_list,
                accountable_team=acc_team_list,
                pillar_kpi_1=pk1_list,
                pillar_kpi_2=pk2_list,
                pillar_kpi_3=pk3_list,
                pillar_kpi_4=pk4_list,
                pillar_kpi_5=pk5_list,
            )

        # Include any markets that might only be in campaigns table if not already populated
        for c_market, c_list in campaigns_by_market.items():
            if c_market not in response:
                response[c_market] = MarketMetadataItem(
                    retailer=[],
                    channel=[],
                    category=[],
                    campaign=c_list,
                    accountable_team=[],
                    pillar_kpi_1=[],
                    pillar_kpi_2=[],
                    pillar_kpi_3=[],
                    pillar_kpi_4=[],
                    pillar_kpi_5=[],
                )

        return response

    def upsert_metadata(
        self, db: Session, payload: MetadataUpsertRequest
    ) -> MetadataOut:
        """
        Adds or updates metadata for a market.
        If market exists, updates retailer, channel, category, accountable_team, pillar_kpi_1..5;
        else creates a new market record.
        Also inserts any campaigns specified into the campaign repository.
        """
        market = payload.market.strip() if payload.market else ""
        if not market:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Market name cannot be empty.",
            )

        def _clean_list(items: Optional[List[str]]) -> List[str]:
            if not items:
                return []
            cleaned = []
            for item in items:
                if item and item.strip() and item.strip() not in cleaned:
                    cleaned.append(item.strip())
            return cleaned

        retailer = _clean_list(payload.retailer)
        channel = _clean_list(payload.channel)
        category = _clean_list(payload.category)
        campaigns = _clean_list(payload.campaign)
        accountable_team = _clean_list(payload.accountable_team)
        pillar_kpi_1 = _clean_list(payload.pillar_kpi_1)
        pillar_kpi_2 = _clean_list(payload.pillar_kpi_2)
        pillar_kpi_3 = _clean_list(payload.pillar_kpi_3)
        pillar_kpi_4 = _clean_list(payload.pillar_kpi_4)
        pillar_kpi_5 = _clean_list(payload.pillar_kpi_5)

        if campaigns:
            existing_campaigns = campaign_repository.get_campaign_names_by_market(
                db, market=[market]
            ).get(market, [])
            for camp_name in campaigns:
                if camp_name not in existing_campaigns:
                    new_camp = Campaign(
                        campaign_id=generate_uuid(),
                        market=market,
                        campaign_name=camp_name,
                        created_by="api",
                        created_at=utcnow(),
                    )
                    campaign_repository.create(db, new_camp)

        metadata_record = metadata_repository.upsert(
            db,
            market=market,
            retailer=retailer,
            channel=channel,
            category=category,
            accountable_team=accountable_team,
            pillar_kpi_1=pillar_kpi_1,
            pillar_kpi_2=pillar_kpi_2,
            pillar_kpi_3=pillar_kpi_3,
            pillar_kpi_4=pillar_kpi_4,
            pillar_kpi_5=pillar_kpi_5,
        )
        db.commit()
        db.refresh(metadata_record)

        current_campaigns = campaign_repository.get_campaign_names_by_market(
            db, market=[market]
        ).get(market, [])

        out = MetadataOut.model_validate(metadata_record)
        out.campaign = current_campaigns
        return out


metadata_service = MetadataService()

