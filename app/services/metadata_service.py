from sqlalchemy.orm import Session

from app.repositories.metadata_repository import MetadataRepository
from app.schemas.metadata_schema import (
    MetadataFilterRequest,
    MetadataFilterResponse,
)


class MetadataService:

    def __init__(self, db: Session):
        self.repository = MetadataRepository(db)

    def get_cascading_metadata(
        self,
        payload: MetadataFilterRequest,
    ) -> MetadataFilterResponse:

        rows = self.repository.get_filtered_metadata(
            market=payload.market,
            retailer=payload.retailer,
            channel=payload.channel,
            category=payload.category,
            campaign=payload.campaign,
        )

        markets = sorted({
            row.market
            for row in rows
            if row.market
        })

        retailers = sorted({
            row.retailer
            for row in rows
            if row.retailer
        })

        channels = sorted({
            row.channel
            for row in rows
            if row.channel
        })

        categories = sorted({
            row.category
            for row in rows
            if row.category
        })

        campaigns = sorted({
            row.campaign
            for row in rows
            if row.campaign
        })

        return MetadataFilterResponse(
            market=markets,
            retailer=retailers,
            channel=channels,
            category=categories,
            campaign=campaigns,
        )