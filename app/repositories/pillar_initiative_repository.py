"""
Repository for PillarInitiative database operations.
"""

from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.models.pillar_initiative import PillarInitiative


class PillarInitiativeRepository:

    def create(self, db: Session, initiative: PillarInitiative) -> PillarInitiative:
        db.add(initiative)
        db.flush()
        return initiative

    def get_by_id(
        self, db: Session, pillar_initiative_id: int
    ) -> Optional[PillarInitiative]:
        return db.get(PillarInitiative, pillar_initiative_id)

    def get_by_initiative_id(
        self, db: Session, initiative_id: str
    ) -> Optional[PillarInitiative]:
        stmt = select(PillarInitiative).where(
            PillarInitiative.initiative_id == initiative_id
        )
        return db.scalars(stmt).first()

    def list_by_pillar(self, db: Session, pillar_id: str) -> list:
        stmt = (
            select(PillarInitiative)
            .where(PillarInitiative.pillar_id == pillar_id)
            .order_by(PillarInitiative.initiative_number)
        )
        return list(db.scalars(stmt).all())

    def count_by_pillar(self, db: Session, pillar_id: str) -> int:
        from sqlalchemy import func
        stmt = (
            select(func.count())
            .select_from(PillarInitiative)
            .where(PillarInitiative.pillar_id == pillar_id)
        )
        return db.scalar(stmt) or 0

    def update(self, db: Session, initiative: PillarInitiative) -> PillarInitiative:
        db.flush()
        return initiative

    def delete(self, db: Session, initiative: PillarInitiative) -> None:
        db.delete(initiative)
        db.flush()

    def delete_by_pillar(self, db: Session, pillar_id: str) -> None:
        initiatives = self.list_by_pillar(db, pillar_id)
        for i in initiatives:
            db.delete(i)
        db.flush()


initiative_repository = PillarInitiativeRepository()
