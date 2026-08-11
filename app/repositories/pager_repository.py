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

    def list_published(
        self,
        db: Session,
        market: Optional[list] = None,
        region: Optional[list] = None,
        channel: Optional[list] = None,
        category: Optional[list] = None,
        campaign_focus: Optional[list] = None,
        pager_type: Optional[list] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list:
        """
        Fetch PUBLISHED pagers with optional multi-select filters.
        Uses selectinload to avoid N+1 queries.
        """
        stmt = (
            select(Pager)
            .where(Pager.status == PagerStatus.PUBLISHED)
            .options(
                selectinload(Pager.pillars).selectinload(Pillar.initiatives)
            )
            .order_by(Pager.published_at.desc())
            .offset(skip)
            .limit(limit)
        )

        if market:
            stmt = stmt.where(Pager.market.in_(market))
        if region:
            stmt = stmt.where(Pager.region.in_(region))
        if channel:
            stmt = stmt.where(Pager.channel.in_(channel))
        if category:
            stmt = stmt.where(Pager.category.in_(category))
        if campaign_focus:
            stmt = stmt.where(Pager.campaign_focus.in_(campaign_focus))
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
