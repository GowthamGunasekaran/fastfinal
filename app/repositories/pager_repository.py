from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models.pager import Pager

class PagerRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, pager: Pager) -> Pager:
        self.db.add(pager)
        self.db.flush()
        return pager

    def get_by_id(self, pager_id: int) -> Pager | None:
        statement = (
            select(Pager)
            .options(selectinload(Pager.pillars))
            .where(Pager.pager_id == pager_id)
        )
        return self.db.scalar(statement)

    def list_pagers(self, status: str | None = None) -> list[Pager]:
        statement = (
            select(Pager)
            .options(selectinload(Pager.pillars))
            .order_by(Pager.pager_id.desc())
        )

        if status:
            statement = statement.where(Pager.status == status)

        return list(self.db.scalars(statement).unique().all())

    def list_by_created_by(
        self,
        created_by: str,
        status: str | None = None,
    ) -> list[Pager]:
        statement = (
            select(Pager)
            .options(selectinload(Pager.pillars))
            .where(Pager.created_by == created_by)
            .order_by(Pager.pager_id.desc())
        )
        if status:
            statement = statement.where(Pager.status == status)
        return list(self.db.scalars(statement).unique().all())

    def list_all_by_created_by(self, created_by: str) -> list[Pager]:
        statement = select(Pager).where(Pager.created_by == created_by)
        return list(self.db.scalars(statement).all())

    def get_published(
        self,
        market: list[str],
        region: list[str],
        channel: list[str],
        category: list[str],
        campaign: list[str],
    ):
        query = (
            select(Pager)
            .options(selectinload(Pager.pillars))
            .where(Pager.status == "PUBLISHED")
        )

        filters = {
            Pager.market: market,
            Pager.region: region,
            Pager.channel: channel,
            Pager.category: category,
            Pager.campaign: campaign,
        }

        for column, values in filters.items():
            if values:
                query = query.where(column.in_(values))

        return list(self.db.scalars(query).unique().all())
