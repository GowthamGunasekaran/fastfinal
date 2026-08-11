"""
Repository for Pager database operations.

Follows repository pattern — no business logic, only DB queries.
IMPORTANT: Methods are named descriptively to avoid shadowing built-in `list`.
"""

from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.models.pager import Pager
from app.db.models.pillar import Pillar
from app.db.models.pillar_initiative import PillarInitiative
from app.utils.enums import PagerStatus


class PagerRepository:

    def create(self, db: Session, pager: Pager) -> Pager:
        db.add(pager)
        db.flush()  # get pager_id without committing
        return pager

    def get_by_id(self, db: Session, pager_id: str) -> Optional[Pager]:
        stmt = (
            select(Pager)
            .where(Pager.pager_id == pager_id)
            .options(
                selectinload(Pager.pillars).selectinload(Pillar.initiatives)
            )
        )
        return db.scalars(stmt).first()

    def get_by_id_simple(self, db: Session, pager_id: str) -> Optional[Pager]:
        """Fetch pager without eager loading relationships."""
        return db.get(Pager, pager_id)

    def list_pagers(
        self,
        db: Session,
        status: Optional[PagerStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list:
        stmt = select(Pager).offset(skip).limit(limit)
        if status is not None:
            stmt = stmt.where(Pager.status == status)
        return list(db.scalars(stmt).all())

    def fetch_all_pagers(
        self,
        db: Session,
        user_id: Optional[list] = None,
        market: Optional[list] = None,
        retailer: Optional[list] = None,
        channel: Optional[list] = None,
        category: Optional[list] = None,
        campaign: Optional[list] = None,
        campaign_focus: Optional[list] = None,
        pager_type: Optional[list] = None,
        status: Optional[list] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list:
        """
        Fetch pager records only (no pillars or initiatives joined).
        Filters by multi-select criteria.
        Defaults to all non-DELETED pagers if no status is specified.
        """
        stmt = (
            select(Pager)
            .order_by(Pager.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        if status:
            stmt = stmt.where(Pager.status.in_(status))
        else:
            stmt = stmt.where(Pager.status != PagerStatus.DELETED)

        if user_id:
            stmt = stmt.where(Pager.created_by.in_(user_id))
        if market:
            stmt = stmt.where(Pager.market.in_(market))
        if retailer:
            stmt = stmt.where(Pager.retailer.in_(retailer))
        if channel:
            stmt = stmt.where(Pager.channel.in_(channel))
        if category:
            stmt = stmt.where(Pager.category.in_(category))

        combined_campaigns = list(set((campaign or []) + (campaign_focus or [])))
        if combined_campaigns:
            stmt = stmt.where(Pager.campaign_focus.in_(combined_campaigns))

        if pager_type:
            stmt = stmt.where(Pager.pager_type.in_(pager_type))

        return list(db.scalars(stmt).all())

    def update(self, db: Session, pager: Pager) -> Pager:
        db.flush()
        return pager

    def delete(self, db: Session, pager: Pager) -> None:
        db.delete(pager)
        db.flush()


pager_repository = PagerRepository()
