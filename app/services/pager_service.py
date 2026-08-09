from collections import defaultdict
from datetime import date
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.db.models.pager import Pager
from app.db.models.pager_pillar_initiative import PagerPillarInitiative
from app.repositories.pager_pillar_initiative_repository import (
    PagerPillarInitiativeRepository,
)
from app.repositories.pager_repository import PagerRepository
from app.schemas.pager_pillar_initiative_schema import StatusUpdate
from app.schemas.pager_schema import (
    InitiativeOut,
    PagerCreate,
    PagerOut,
    PagerUpdate,
    PillarOut,
    UserPagerSummary,
)
from app.utils.constants import (
    ALLOWED_SCORING_MODES,
    ALLOWED_STATUSES,
    DELETED_STATUS,
    DRAFT_STATUS,
    PUBLISHED_STATUS,
    WEIGHTED_MODE,
)
from app.utils.validators import validate_pager_structure, validate_status


class PagerService:
    def __init__(self, db: Session):
        self.db = db
        self.pager_repo = PagerRepository(db)
        self.child_repo = PagerPillarInitiativeRepository(db)

    def create_pager(self, payload: PagerCreate) -> PagerOut:
        validate_pager_structure(payload.scoring_mode, payload.pillars)

        pager = Pager(
            market=payload.market,
            category=payload.category,
            campaign_focus=payload.campaign_focus,
            channel=payload.channel,
            title=payload.title,
            business_outcome_statement=payload.business_outcome_statement,
            scoring_mode=payload.scoring_mode,
            status=payload.status,
            created_by=payload.created_by,
            updated_by=payload.created_by,
        )

        try:
            self.pager_repo.add(pager)

            pillar_ids = {}
            for pillar in payload.pillars:
                pillar_ids[pillar.pillar_number] = str(uuid4())
                for initiative in pillar.initiatives:
                    self.child_repo.add(
                        PagerPillarInitiative(
                            pager_id=pager.pager_id,
                            pillar_id=pillar_ids[pillar.pillar_number],
                            pillar_number=pillar.pillar_number,
                            pillar_name=pillar.pillar_name,
                            pillar_description=pillar.pillar_description,
                            pillar_weight=pillar.pillar_weight,
                            initiative_id=str(uuid4()),
                            initiative_number=initiative.initiative_number,
                            priority_level=initiative.priority_level,
                            accountable_function_department=initiative.accountable_function_department,
                            initiative_description=initiative.initiative_description,
                            kpi_metric=initiative.kpi_metric,
                            success_target=initiative.success_target,
                            unit=initiative.unit,
                            week_start=self._date(initiative.week_start),
                            week_end=self._date(initiative.week_end),
                            guidelines=initiative.guidelines,
                            checklist_compliance_notes=initiative.checklist_compliance_notes,
                            image_urls=initiative.image_urls,
                            status=payload.status,
                            created_by=payload.created_by,
                            updated_by=payload.created_by,
                        )
                    )

            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        return self._response(self._get_or_404(pager.pager_id))

    def update_pager(self, pager_id: int, payload: PagerUpdate) -> PagerOut:
        pager = self._get_or_404(pager_id)
        scoring_mode = payload.scoring_mode or pager.scoring_mode

        if payload.pillars is not None:
            # During edit, only the submitted pillars/initiatives are validated.
            # A partial edit must not require all 5 weighted pillars to be resent.
            validate_pager_structure(
                scoring_mode,
                payload.pillars,
                require_all_weighted_pillars=False,
            )

        for field in (
            "market",
            "category",
            "campaign_focus",
            "channel",
            "title",
            "business_outcome_statement",
            "scoring_mode",
            "status",
        ):
            value = getattr(payload, field)
            if value is not None:
                setattr(pager, field, value)

        pager.updated_by = payload.updated_by

        if payload.pillars is not None:
            for pillar in payload.pillars:
                for initiative in pillar.initiatives:
                    row = self.child_repo.get_by_key(
                        pager_id,
                        pillar.pillar_number,
                        initiative.initiative_number,
                    )

                    if row is None:
                        row = PagerPillarInitiative(
                            pager_id=pager_id,
                            pillar_id=pillar.pillar_id or str(uuid4()),
                            pillar_number=pillar.pillar_number,
                            initiative_id=initiative.initiative_id or str(uuid4()),
                            initiative_number=initiative.initiative_number,
                            created_by=payload.updated_by,
                            updated_by=payload.updated_by,
                            status=pager.status,
                        )
                        self.child_repo.add(row)

                    row.pillar_id = pillar.pillar_id or row.pillar_id
                    row.pillar_number = pillar.pillar_number
                    row.pillar_name = pillar.pillar_name
                    row.pillar_description = pillar.pillar_description
                    row.pillar_weight = pillar.pillar_weight

                    row.initiative_id = initiative.initiative_id or row.initiative_id
                    row.initiative_number = initiative.initiative_number
                    row.priority_level = initiative.priority_level
                    row.accountable_function_department = initiative.accountable_function_department
                    row.initiative_description = initiative.initiative_description
                    row.kpi_metric = initiative.kpi_metric
                    row.success_target = initiative.success_target
                    row.unit = initiative.unit
                    row.week_start = self._date(initiative.week_start)
                    row.week_end = self._date(initiative.week_end)
                    row.guidelines = initiative.guidelines
                    row.checklist_compliance_notes = initiative.checklist_compliance_notes
                    row.image_urls = initiative.image_urls
                    row.status = pager.status
                    row.updated_by = payload.updated_by

        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        return self._response(self._get_or_404(pager_id))

    def update_status(self, pager_id: int, payload: StatusUpdate) -> PagerOut:
        validate_status(payload.status)
        pager = self._get_or_404(pager_id)

        if payload.status == PUBLISHED_STATUS:
            children = self.child_repo.list_by_pager(pager_id)
            if pager.scoring_mode == WEIGHTED_MODE:
                pillar_numbers = {row.pillar_number for row in children}
                total_weight = sum(
                    row.pillar_weight or 0
                    for row in children
                    if row.initiative_number == 1
                )
                if pillar_numbers != {1, 2, 3, 4, 5}:
                    raise HTTPException(
                        status_code=422,
                        detail="All 5 pillars are required before publishing a weighted pager.",
                    )
                if abs(total_weight - 100) > 0.001:
                    raise HTTPException(
                        status_code=422,
                        detail=f"Pillar weights must total 100 before publishing. Current total: {total_weight}.",
                    )

        pager.status = payload.status
        pager.updated_by = payload.updated_by

        for row in pager.pillars:
            row.status = payload.status
            row.updated_by = payload.updated_by

        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        return self._response(self._get_or_404(pager_id))

    def get_pagers(self, status: str | None = None) -> list[PagerOut]:
        normalized = self._normalize_status(status)
        return [self._response(p) for p in self.pager_repo.list_pagers(normalized)]

    def get_pager(self, pager_id: int) -> PagerOut:
        return self._response(self._get_or_404(pager_id))

    def get_user_pagers(
        self,
        user_id: str,
        status: str | None = None,
    ) -> UserPagerSummary:
        normalized = self._normalize_status(status)
        pagers = self.pager_repo.list_by_created_by(user_id, normalized)
        all_pagers = self.pager_repo.list_all_by_created_by(user_id)

        counts = defaultdict(int)
        for pager in all_pagers:
            counts[pager.status] += 1

        return UserPagerSummary(
            created_by=user_id,
            total=len(all_pagers),
            draft=counts[DRAFT_STATUS],
            published=counts[PUBLISHED_STATUS],
            deleted=counts[DELETED_STATUS],
            archived=counts["ARCHIVED"],
            pagers=[self._response(p) for p in pagers],
        )

    def _get_or_404(self, pager_id: int) -> Pager:
        pager = self.pager_repo.get_by_id(pager_id)
        if pager is None:
            raise HTTPException(status_code=404, detail="Pager not found.")
        return pager

    @staticmethod
    def _normalize_status(status: str | None) -> str | None:
        if status is None:
            return None
        validate_status(status)
        return status.upper()

    @staticmethod
    def _date(value: str | None):
        return date.fromisoformat(value) if value else None

    @staticmethod
    def _response(pager: Pager) -> PagerOut:
        grouped = defaultdict(list)
        pillar_data = {}

        for row in pager.pillars:
            grouped[row.pillar_number].append(
                InitiativeOut(
                    pillar_initiative_id=row.pillar_initiative_id,
                    initiative_id=row.initiative_id,
                    initiative_number=row.initiative_number,
                    priority_level=row.priority_level,
                    accountable_function_department=row.accountable_function_department,
                    initiative_description=row.initiative_description,
                    kpi_metric=row.kpi_metric,
                    success_target=row.success_target,
                    unit=row.unit,
                    week_start=row.week_start.isoformat() if row.week_start else None,
                    week_end=row.week_end.isoformat() if row.week_end else None,
                    guidelines=row.guidelines,
                    checklist_compliance_notes=row.checklist_compliance_notes,
                    image_urls=row.image_urls or [],
                    status=row.status,
                )
            )
            if row.pillar_number not in pillar_data:
                pillar_data[row.pillar_number] = {
                    "pillar_id": row.pillar_id,
                    "pillar_number": row.pillar_number,
                    "pillar_name": row.pillar_name,
                    "pillar_description": row.pillar_description,
                    "pillar_weight": row.pillar_weight,
                }

        pillars = [
            PillarOut(**pillar_data[number], initiatives=grouped[number])
            for number in sorted(pillar_data)
        ]

        return PagerOut(
            pager_id=pager.pager_id,
            market=pager.market,
            category=pager.category,
            campaign_focus=pager.campaign_focus,
            channel=pager.channel,
            title=pager.title,
            business_outcome_statement=pager.business_outcome_statement,
            scoring_mode=pager.scoring_mode,
            status=pager.status,
            created_at=pager.created_at,
            created_by=pager.created_by,
            updated_at=pager.updated_at,
            updated_by=pager.updated_by,
            pillars=pillars,
        )

def get_published(
    self,
    market: list[str],
    region: list[str],
    channel: list[str],
    category: list[str],
    campaign: list[str],
):
    return self.pager_repository.get_published(
        market,
        region,
        channel,
        category,
        campaign,
    )