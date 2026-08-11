"""
Service for the Update Track API.

Handles the decision logic for which table/column to update,
validation of required IDs, and audit field updates.
"""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.track_repository import track_repository
from app.schemas.track_schema import UpdateTrackRequest, UpdateTrackResponse
from app.utils.helpers import utcnow


class TrackService:

    def update_track(self, db: Session, payload: UpdateTrackRequest) -> UpdateTrackResponse:
        """
        Route to correct update branch based on payload.table, then commit.
        Rolls back automatically if an exception is raised (FastAPI/SQLAlchemy handles this
        when the session is provided via Depends(get_db) with its try/finally block).
        """
        try:
            if payload.table == "pager":
                return self._update_pager_track(db, payload)
            elif payload.table == "pillar":
                return self._update_pillar_track(db, payload)
            else:  # initiative
                return self._update_initiative_track(db, payload)
        except HTTPException:
            db.rollback()
            raise
        except Exception as exc:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _update_pager_track(self, db: Session, payload: UpdateTrackRequest) -> UpdateTrackResponse:
        pager = track_repository.get_pager(db, payload.pager_id)
        if not pager:
            raise HTTPException(status_code=404, detail="Pager not found")

        pager.track = payload.track
        pager.updated_by = payload.updated_by
        pager.updated_at = utcnow()

        db.commit()
        db.refresh(pager)

        return UpdateTrackResponse(
            table="pager",
            pager_id=pager.pager_id,
            pillar_id=None,
            initiative_id=None,
            track=pager.track,
            updated_by=payload.updated_by,
        )

    def _update_pillar_track(self, db: Session, payload: UpdateTrackRequest) -> UpdateTrackResponse:
        pillar = track_repository.get_pillar(db, payload.pager_id, payload.pillar_id)
        if not pillar:
            raise HTTPException(
                status_code=404,
                detail="Pillar not found for the specified pager",
            )

        pillar.pillar_track = payload.track
        # Pillar model has updated_at but no updated_by column
        pillar.updated_at = utcnow()

        db.commit()
        db.refresh(pillar)

        return UpdateTrackResponse(
            table="pillar",
            pager_id=pillar.pager_id,
            pillar_id=pillar.pillar_id,
            initiative_id=None,
            track=pillar.pillar_track,
            updated_by=payload.updated_by,
        )

    def _update_initiative_track(self, db: Session, payload: UpdateTrackRequest) -> UpdateTrackResponse:
        initiative = track_repository.get_initiative(
            db, payload.pager_id, payload.pillar_id, payload.initiative_id
        )
        if not initiative:
            raise HTTPException(
                status_code=404,
                detail="Initiative not found for the specified pager and pillar",
            )

        initiative.initiative_track = payload.track
        # PillarInitiative model has updated_at but no updated_by column
        initiative.updated_at = utcnow()

        db.commit()
        db.refresh(initiative)

        return UpdateTrackResponse(
            table="initiative",
            pager_id=initiative.pager_id,
            pillar_id=initiative.pillar_id,
            initiative_id=initiative.initiative_id,
            track=initiative.initiative_track,
            updated_by=payload.updated_by,
        )


track_service = TrackService()
