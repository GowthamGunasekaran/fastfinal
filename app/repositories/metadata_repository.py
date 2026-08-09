from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.metadata import Metadata


class MetadataRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_filtered_metadata(
        self,
        market: list[str],
        retailer: list[str],
        channel: list[str],
        category: list[str],
        campaign: list[str],
    ) -> list[Metadata]:

        statement = select(Metadata)

        if market:
            statement = statement.where(
                Metadata.market.in_(market)
            )

        if retailer:
            statement = statement.where(
                Metadata.retailer.in_(retailer)
            )

        if channel:
            statement = statement.where(
                Metadata.channel.in_(channel)
            )

        if category:
            statement = statement.where(
                Metadata.category.in_(category)
            )

        if campaign:
            statement = statement.where(
                Metadata.campaign.in_(campaign)
            )

        return list(self.db.scalars(statement).all())