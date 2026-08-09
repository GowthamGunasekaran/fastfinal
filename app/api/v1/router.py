from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.pager_pillar_initiative_schema import StatusUpdate
from app.schemas.pager_schema import PagerCreate, PagerOut, PagerUpdate, UserPagerSummary
from app.services.pager_service import PagerService
from app.schemas.metadata_schema import (
    MetadataFilterRequest,
    MetadataFilterResponse,
)
from app.services.metadata_service import MetadataService
router = APIRouter(tags=["Pagers"])


def get_service(db: Session = Depends(get_db)) -> PagerService:
    return PagerService(db)


@router.post("/pagers", response_model=PagerOut, status_code=201)
def create_pager(
    payload: PagerCreate,
    service: PagerService = Depends(get_service),
):
    return service.create_pager(payload)

@router.post(
    "/metadata/filter",
    response_model=MetadataFilterResponse,
)
def filter_metadata(
    payload: MetadataFilterRequest,
    db: Session = Depends(get_db),
):
    service = MetadataService(db)
    return service.get_cascading_metadata(payload)

@router.put("/pagers/{pager_id}", response_model=PagerOut)
def update_pager(
    pager_id: int,
    payload: PagerUpdate,
    service: PagerService = Depends(get_service),
):
    return service.update_pager(pager_id, payload)


@router.patch("/pagers/{pager_id}/status", response_model=PagerOut)
def update_pager_status(
    pager_id: int,
    payload: StatusUpdate,
    service: PagerService = Depends(get_service),
):
    return service.update_status(pager_id, payload)


@router.get("/pagers", response_model=list[PagerOut])
def get_pagers(
    status: str | None = Query(default=None),
    service: PagerService = Depends(get_service),
):
    return service.get_pagers(status)


@router.get("/pagers/{pager_id}", response_model=PagerOut)
def get_pager(
    pager_id: int,
    service: PagerService = Depends(get_service),
):
    return service.get_pager(pager_id)


@router.get("/users/{user_id}/pagers", response_model=UserPagerSummary)
def get_user_pagers(
    user_id: str,
    status: str | None = Query(default=None),
    service: PagerService = Depends(get_service),
):
    return service.get_user_pagers(user_id, status)

@router.get("/landing-page")
def get_landing_page(
    market: list[str] = Query(default=[]),
    region: list[str] = Query(default=[]),
    channel: list[str] = Query(default=[]),
    category: list[str] = Query(default=[]),
    campaign: list[str] = Query(default=[]),
    db: Session = Depends(get_db),
):
    return PagerService(db).get_published(
        market,
        region,
        channel,
        category,
        campaign,
    )