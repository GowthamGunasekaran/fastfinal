"""
Pager service — business logic for creating, editing, and managing pagers.

Transaction safety: all related inserts happen in one db session.
The router commits only after the service returns successfully.
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.db.models.pager import Pager
from app.db.models.pillar import Pillar
from app.db.models.pillar_initiative import PillarInitiative
from app.repositories.pager_repository import pager_repository
from app.repositories.pillar_repository import pillar_repository
from app.repositories.pillar_initiative_repository import initiative_repository
from app.schemas.pager_schema import (
    PagerCreate,
    PagerUpdate,
    PagerOut,
    FetchAllPagersRequest,
    FetchAllPagersResponse,
)
from app.utils.enums import PagerStatus, ScoringMode
from app.utils.helpers import generate_uuid, utcnow
from app.utils.validators import (
    validate_image_urls,
    validate_pillar_count,
    validate_initiative_count,
    validate_weighted_total,
)


class PagerService:

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def create_pager(self, db: Session, payload: PagerCreate) -> Pager:
        pillars_data = payload.pillars or []

        # Validate pillar count
        validate_pillar_count(len(pillars_data))

        # Validate initiative counts early
        for pillar_data in pillars_data:
            validate_initiative_count(
                len(pillar_data.initiatives or []), pillar_data.pillar_number
            )
            for init_data in pillar_data.initiatives or []:
                validate_image_urls(init_data.image_urls or [])

        published_by = payload.published_by
        published_at = payload.published_at

        if payload.status == PagerStatus.PUBLISHED:
            if published_by is None:
                published_by = payload.created_by
            if published_at is None:
                published_at = utcnow()

        # Create pager
        pager = Pager(
            pager_id=generate_uuid(),
            title=payload.title,
            market=payload.market,
            retailer=payload.retailer,
            channel=payload.channel,
            category=payload.category,
            campaign_focus=payload.campaign_focus,
            business_outcome_statement=payload.business_outcome_statement,
            scoring_mode=payload.scoring_mode,
            status=payload.status,
            track=payload.track,
            pager_type=payload.pager_type,
            image_url=payload.image_url,
            created_by=payload.created_by,
            published_by=published_by,
            published_at=published_at,
            created_at=utcnow(),
            updated_at=utcnow(),
        )
        pager_repository.create(db, pager)

        # Create pillars and initiatives
        for pillar_data in pillars_data:
            pillar = Pillar(
                pillar_id=generate_uuid(),
                pager_id=pager.pager_id,
                pillar_number=pillar_data.pillar_number,
                pillar_name=pillar_data.pillar_name,
                pillar_description=pillar_data.pillar_description,
                pillar_weight=pillar_data.pillar_weight,
                pillar_track=pillar_data.pillar_track,
                created_at=utcnow(),
                updated_at=utcnow(),
            )
            pillar_repository.create(db, pillar)

            for init_data in pillar_data.initiatives or []:
                initiative = PillarInitiative(
                    initiative_id=generate_uuid(),
                    pager_id=pager.pager_id,
                    pillar_id=pillar.pillar_id,
                    initiative_number=init_data.initiative_number,
                    initiative_track=init_data.initiative_track,
                    priority_level=init_data.priority_level,
                    accountable_function_department=init_data.accountable_function_department,
                    initiative_description=init_data.initiative_description,
                    kpi_metric=init_data.kpi_metric,
                    success_target=init_data.success_target,
                    unit=init_data.unit,
                    week_start=init_data.week_start,
                    week_end=init_data.week_end,
                    guidelines=init_data.guidelines,
                    checklist_compliance_notes=init_data.checklist_compliance_notes,
                    image_urls=init_data.image_urls or [],
                    created_at=utcnow(),
                    updated_at=utcnow(),
                )
                initiative_repository.create(db, initiative)

        db.commit()
        # Reload with relationships
        return pager_repository.get_by_id(db, pager.pager_id)

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_pager(self, db: Session, pager_id: str) -> Pager:
        pager = pager_repository.get_by_id(db, pager_id)
        if not pager:
            raise HTTPException(status_code=404, detail="Pager not found.")
        return pager

    def list_pagers(
        self,
        db: Session,
        status: Optional[PagerStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list:
        return pager_repository.list_pagers(db, status=status, skip=skip, limit=limit)

    def fetch_all_pagers(
        self,
        db: Session,
        filters: "FetchAllPagersRequest",
        skip: int = 0,
        limit: int = 100,
    ) -> "FetchAllPagersResponse":
        from app.schemas.pager_schema import FetchAllPagersResponse
        pagers = pager_repository.fetch_all_pagers(
            db,
            user_id=filters.user_id or [],
            market=filters.market or [],
            retailer=filters.retailer or [],
            channel=filters.channel or [],
            category=filters.category or [],
            campaign=filters.campaign or [],
            campaign_focus=filters.campaign_focus or [],
            pager_type=filters.pager_type or [],
            status=filters.status or [],
            skip=skip,
            limit=limit,
        )
        return FetchAllPagersResponse(total=len(pagers), pagers=pagers)

    # ------------------------------------------------------------------
    # Update (PATCH)
    # ------------------------------------------------------------------

    def update_pager(self, db: Session, pager_id: str, payload: PagerUpdate) -> Pager:
        pager = pager_repository.get_by_id(db, pager_id)
        if not pager:
            raise HTTPException(status_code=404, detail="Pager not found.")

        if pager.status == PagerStatus.DELETED:
            raise HTTPException(status_code=400, detail="Cannot edit a deleted pager.")

        # Update pager scalar fields
        update_data = payload.model_dump(exclude={"pillars"}, exclude_none=True)
        for field, value in update_data.items():
            setattr(pager, field, value)
        pager.updated_at = utcnow()

        if pager.status == PagerStatus.PUBLISHED:
            if pager.published_by is None:
                pager.published_by = payload.updated_by or pager.created_by
            if pager.published_at is None:
                pager.published_at = utcnow()

        # Handle pillars if provided
        if payload.pillars is not None:
            self._sync_pillars(db, pager, payload.pillars)

        db.commit()
        return pager_repository.get_by_id(db, pager.pager_id)

    def _sync_pillars(self, db: Session, pager: Pager, pillars_data: list) -> None:
        """
        Sync pillars: update existing, create new, remove omitted.
        Uses pillar_id to identify existing pillars.
        """
        validate_pillar_count(len(pillars_data))

        existing_pillars = {p.pillar_id: p for p in pager.pillars}
        submitted_pillar_ids = set()

        for pillar_data in pillars_data:
            validate_initiative_count(
                len(pillar_data.initiatives or []), pillar_data.pillar_number or 0
            )
            for init_data in pillar_data.initiatives or []:
                validate_image_urls(init_data.image_urls or [])

            if pillar_data.pillar_id and pillar_data.pillar_id in existing_pillars:
                # Update existing pillar
                pillar = existing_pillars[pillar_data.pillar_id]
                submitted_pillar_ids.add(pillar.pillar_id)
                if pillar_data.pillar_number is not None:
                    pillar.pillar_number = pillar_data.pillar_number
                if pillar_data.pillar_name is not None:
                    pillar.pillar_name = pillar_data.pillar_name
                if pillar_data.pillar_description is not None:
                    pillar.pillar_description = pillar_data.pillar_description
                if pillar_data.pillar_weight is not None:
                    pillar.pillar_weight = pillar_data.pillar_weight
                if pillar_data.pillar_track is not None:
                    pillar.pillar_track = pillar_data.pillar_track
                pillar.updated_at = utcnow()

                if pillar_data.initiatives is not None:
                    self._sync_initiatives(db, pager, pillar, pillar_data.initiatives)
            else:
                # Create new pillar
                new_pillar = Pillar(
                    pillar_id=generate_uuid(),
                    pager_id=pager.pager_id,
                    pillar_number=pillar_data.pillar_number or 1,
                    pillar_name=pillar_data.pillar_name,
                    pillar_description=pillar_data.pillar_description,
                    pillar_weight=pillar_data.pillar_weight,
                    pillar_track=pillar_data.pillar_track,
                    created_at=utcnow(),
                    updated_at=utcnow(),
                )
                pillar_repository.create(db, new_pillar)
                submitted_pillar_ids.add(new_pillar.pillar_id)

                for init_data in pillar_data.initiatives or []:
                    initiative = PillarInitiative(
                        initiative_id=generate_uuid(),
                        pager_id=pager.pager_id,
                        pillar_id=new_pillar.pillar_id,
                        initiative_number=init_data.initiative_number,
                        initiative_track=init_data.initiative_track,
                        priority_level=init_data.priority_level,
                        accountable_function_department=init_data.accountable_function_department,
                        initiative_description=init_data.initiative_description,
                        kpi_metric=init_data.kpi_metric,
                        success_target=init_data.success_target,
                        unit=init_data.unit,
                        week_start=init_data.week_start,
                        week_end=init_data.week_end,
                        guidelines=init_data.guidelines,
                        checklist_compliance_notes=init_data.checklist_compliance_notes,
                        image_urls=init_data.image_urls or [],
                        created_at=utcnow(),
                        updated_at=utcnow(),
                    )
                    initiative_repository.create(db, initiative)

        # Remove pillars not in submission
        for pillar_id, pillar in existing_pillars.items():
            if pillar_id not in submitted_pillar_ids:
                pillar_repository.delete(db, pillar)

    def _sync_initiatives(
        self, db: Session, pager: Pager, pillar: Pillar, initiatives_data: list
    ) -> None:
        """
        Sync initiatives for a specific pillar.
        Uses initiative_id to identify existing initiatives.
        """
        existing = {i.initiative_id: i for i in pillar.initiatives}
        submitted_ids = set()

        for init_data in initiatives_data:
            if init_data.initiative_id and init_data.initiative_id in existing:
                # Update existing
                initiative = existing[init_data.initiative_id]
                submitted_ids.add(initiative.initiative_id)
                fields = [
                    "initiative_number", "initiative_track", "priority_level",
                    "accountable_function_department", "initiative_description",
                    "kpi_metric", "success_target", "unit", "week_start", "week_end",
                    "guidelines", "checklist_compliance_notes", "image_urls",
                ]
                for f in fields:
                    val = getattr(init_data, f, None)
                    if val is not None:
                        setattr(initiative, f, val)
                initiative.updated_at = utcnow()
            else:
                # Create new
                new_initiative = PillarInitiative(
                    initiative_id=generate_uuid(),
                    pager_id=pager.pager_id,
                    pillar_id=pillar.pillar_id,
                    initiative_number=init_data.initiative_number or 1,
                    initiative_track=init_data.initiative_track,
                    priority_level=init_data.priority_level,
                    accountable_function_department=init_data.accountable_function_department,
                    initiative_description=init_data.initiative_description,
                    kpi_metric=init_data.kpi_metric,
                    success_target=init_data.success_target,
                    unit=init_data.unit,
                    week_start=init_data.week_start,
                    week_end=init_data.week_end,
                    guidelines=init_data.guidelines,
                    checklist_compliance_notes=init_data.checklist_compliance_notes,
                    image_urls=init_data.image_urls or [],
                    created_at=utcnow(),
                    updated_at=utcnow(),
                )
                initiative_repository.create(db, new_initiative)
                submitted_ids.add(new_initiative.initiative_id)

        # Remove initiatives not submitted
        for init_id, initiative in existing.items():
            if init_id not in submitted_ids:
                initiative_repository.delete(db, initiative)

    # ------------------------------------------------------------------
    # Status Update
    # ------------------------------------------------------------------

    def update_status(
        self,
        db: Session,
        pager_id: str,
        new_status: PagerStatus,
        updated_by: Optional[str] = None,
        published_by: Optional[str] = None,
        published_at: Optional[datetime] = None,
    ) -> Pager:
        pager = pager_repository.get_by_id(db, pager_id)
        if not pager:
            raise HTTPException(status_code=404, detail="Pager not found.")

        self._validate_status_transition(pager, new_status)

        if published_by is not None:
            pager.published_by = published_by
        if published_at is not None:
            pager.published_at = published_at

        if new_status == PagerStatus.PUBLISHED:
            self._validate_for_publish(pager)
            if pager.published_by is None:
                pager.published_by = published_by if published_by is not None else updated_by
            if pager.published_at is None:
                pager.published_at = published_at if published_at is not None else utcnow()

        pager.status = new_status
        pager.updated_by = updated_by
        pager.updated_at = utcnow()

        db.commit()
        return pager_repository.get_by_id(db, pager.pager_id)

    def _validate_status_transition(self, pager: Pager, new_status: PagerStatus) -> None:
        if pager.status == PagerStatus.DELETED:
            raise HTTPException(
                status_code=400,
                detail="Cannot change status of a deleted pager.",
            )
        if pager.status == new_status:
            raise HTTPException(
                status_code=400,
                detail=f"Pager is already in status '{new_status}'.",
            )

    def _validate_for_publish(self, pager: Pager) -> None:
        if not pager.pillars:
            raise HTTPException(
                status_code=400,
                detail="Cannot publish: pager has no pillars.",
            )
        if len(pager.pillars) > 5:
            raise HTTPException(
                status_code=400,
                detail="Cannot publish: more than 5 pillars.",
            )
        for pillar in pager.pillars:
            if len(pillar.initiatives) > 3:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot publish: pillar {pillar.pillar_number} has more than 3 initiatives.",
                )
        if pager.scoring_mode == ScoringMode.WEIGHTED:
            validate_weighted_total(pager.pillars)


pager_service = PagerService()
