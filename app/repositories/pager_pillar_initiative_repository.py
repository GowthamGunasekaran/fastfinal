from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.pager_pillar_initiative import PagerPillarInitiative


class PagerPillarInitiativeRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, row: PagerPillarInitiative) -> PagerPillarInitiative:
        self.db.add(row)
        return row

    def list_by_pager(self, pager_id: int) -> list[PagerPillarInitiative]:
        statement = (
            select(PagerPillarInitiative)
            .where(PagerPillarInitiative.pager_id == pager_id)
            .order_by(
                PagerPillarInitiative.pillar_number,
                PagerPillarInitiative.initiative_number,
            )
        )
        return list(self.db.scalars(statement).all())

    def get_by_key(
        self,
        pager_id: int,
        pillar_number: int,
        initiative_number: int,
    ) -> PagerPillarInitiative | None:
        statement = select(PagerPillarInitiative).where(
            PagerPillarInitiative.pager_id == pager_id,
            PagerPillarInitiative.pillar_number == pillar_number,
            PagerPillarInitiative.initiative_number == initiative_number,
        )
        return self.db.scalar(statement)
