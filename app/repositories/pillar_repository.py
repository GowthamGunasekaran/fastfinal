"""
Repository for Pillar database operations.
"""

from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.models.pillar import Pillar


class PillarRepository:

    def create(self, db: Session, pillar: Pillar) -> Pillar:
        db.add(pillar)
        db.flush()
        return pillar

    def get_by_id(self, db: Session, pillar_id: str) -> Optional[Pillar]:
        stmt = (
            select(Pillar)
            .where(Pillar.pillar_id == pillar_id)
            .options(selectinload(Pillar.initiatives))
        )
        return db.scalars(stmt).first()

    def list_by_pager(self, db: Session, pager_id: str) -> list:
        stmt = (
            select(Pillar)
            .where(Pillar.pager_id == pager_id)
            .options(selectinload(Pillar.initiatives))
            .order_by(Pillar.pillar_number)
        )
        return list(db.scalars(stmt).all())

    def count_by_pager(self, db: Session, pager_id: str) -> int:
        from sqlalchemy import func
        stmt = select(func.count()).select_from(Pillar).where(Pillar.pager_id == pager_id)
        return db.scalar(stmt) or 0

    def update(self, db: Session, pillar: Pillar) -> Pillar:
        db.flush()
        return pillar

    def delete(self, db: Session, pillar: Pillar) -> None:
        db.delete(pillar)
        db.flush()

    def delete_by_pager(self, db: Session, pager_id: str) -> None:
        pillars = self.list_by_pager(db, pager_id)
        for p in pillars:
            db.delete(p)
        db.flush()


pillar_repository = PillarRepository()
