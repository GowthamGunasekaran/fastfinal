"""
Repository for the Update Track API.

Provides focused query methods that enforce the full hierarchy:
  pager_id
  pager_id + pillar_id
  pager_id + pillar_id + initiative_id
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.pager import Pager
from app.db.models.pillar import Pillar
from app.db.models.pillar_initiative import PillarInitiative


class TrackRepository:

    # ------------------------------------------------------------------
    # Pager
    # ------------------------------------------------------------------

    def get_pager(self, db: Session, pager_id: str) -> Optional[Pager]:
        """Fetch a Pager by its primary key."""
        stmt = select(Pager).where(Pager.pager_id == pager_id)
        return db.execute(stmt).scalars().first()

    # ------------------------------------------------------------------
    # Pillar  (must belong to the given pager)
    # ------------------------------------------------------------------

    def get_pillar(self, db: Session, pager_id: str, pillar_id: str) -> Optional[Pillar]:
        """Fetch a Pillar using BOTH pager_id AND pillar_id."""
        stmt = select(Pillar).where(
            Pillar.pager_id == pager_id,
            Pillar.pillar_id == pillar_id,
        )
        return db.execute(stmt).scalars().first()

    # ------------------------------------------------------------------
    # Initiative  (must belong to the given pager AND pillar)
    # ------------------------------------------------------------------

    def get_initiative(
        self,
        db: Session,
        pager_id: str,
        pillar_id: str,
        initiative_id: str,
    ) -> Optional[PillarInitiative]:
        """Fetch an Initiative using pager_id, pillar_id AND initiative_id."""
        stmt = select(PillarInitiative).where(
            PillarInitiative.pager_id == pager_id,
            PillarInitiative.pillar_id == pillar_id,
            PillarInitiative.initiative_id == initiative_id,
        )
        return db.execute(stmt).scalars().first()


track_repository = TrackRepository()
