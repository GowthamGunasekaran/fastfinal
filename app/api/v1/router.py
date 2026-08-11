"""
API v1 router — all routes registered here and included in main.py.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from app.db.database import get_db
from app.schemas.pager_schema import (
    PagerCreate,
    PagerUpdate,
    PagerOut,
    PagerSummary,
    StatusUpdate,
)
from app.schemas.metadata_schema import MetadataFilterRequest, MetadataFilterResponse
from app.schemas.landing_page_schema import LandingPageFilterRequest, LandingPageResponse
from app.services.pager_service import pager_service
from app.services.metadata_service import metadata_service
from app.services.landing_page_service import landing_page_service
from app.utils.enums import PagerStatus

router = APIRouter(prefix="/api/v1")


# ==========================================================================
# PAGER ENDPOINTS
# ==========================================================================

@router.post(
    "/pagers",
    response_model=PagerOut,
    summary="Create a new Pager with optional Pillars and Initiatives",
    tags=["Pagers"],
)
def create_pager(payload: PagerCreate, db: Session = Depends(get_db)):
    """
    Create a Pager (status: DRAFT by default) with up to 5 Pillars
    and up to 3 Initiatives per Pillar.

    - Partial creation is allowed (fewer than 5 pillars, etc.)
    - All inserts are in a single transaction; any failure rolls back everything.
    """
    return pager_service.create_pager(db, payload)


@router.get(
    "/pagers",
    response_model=List[PagerSummary],
    summary="List all pagers (admin)",
    tags=["Pagers"],
)
def list_pagers(
    status: Optional[PagerStatus] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """List pagers — admin endpoint. Supports optional status filter."""
    return pager_service.list_pagers(db, status=status, skip=skip, limit=limit)


@router.get(
    "/pagers/{pager_id}",
    response_model=PagerOut,
    summary="Get a single Pager with full Pillars and Initiatives",
    tags=["Pagers"],
)
def get_pager(pager_id: str, db: Session = Depends(get_db)):
    return pager_service.get_pager(db, pager_id)


@router.patch(
    "/pagers/{pager_id}",
    response_model=PagerOut,
    summary="Partially update a Pager (fields, pillars, initiatives, images)",
    tags=["Pagers"],
)
def update_pager(
    pager_id: str, payload: PagerUpdate, db: Session = Depends(get_db)
):
    """
    Partial update for a Pager.

    - Pager fields updated if provided.
    - Pillars synced if `pillars` array is provided:
      - Existing pillars (matched by `pillar_id`) are updated.
      - New pillars (no `pillar_id`) are created.
      - Pillars absent from the payload are removed.
    - Initiatives synced similarly within each pillar.
    """
    return pager_service.update_pager(db, pager_id, payload)


@router.patch(
    "/pagers/{pager_id}/status",
    response_model=PagerOut,
    summary="Update pager status (DRAFT/PUBLISHED/DELETED/ARCHIVED)",
    tags=["Pagers"],
)
def update_pager_status(
    pager_id: str, payload: StatusUpdate, db: Session = Depends(get_db)
):
    """
    Update the status of a Pager.

    - PUBLISHED: validates pillar count, weighted total, initiative counts.
    - DELETED / ARCHIVED: soft status change only.
    """
    return pager_service.update_status(
        db, pager_id, payload.status, payload.updated_by
    )


# ==========================================================================
# LANDING PAGE ENDPOINT
# ==========================================================================

@router.post(
    "/landing",
    response_model=LandingPageResponse,
    summary="Landing page — get published pagers with multi-select filters",
    tags=["Landing Page"],
)
def landing_page(
    filters: LandingPageFilterRequest,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """
    Returns only PUBLISHED pagers with full pillar/initiative tree.

    - Multi-select filters supported for all metadata dimensions.
    - Empty list = no filter (return all published).
    - Uses SQLAlchemy selectinload to avoid N+1 queries.
    """
    return landing_page_service.get_published_pagers(db, filters, skip=skip, limit=limit)


# ==========================================================================
# METADATA CASCADING ENDPOINT
# ==========================================================================

@router.post(
    "/metadata/filter",
    response_model=MetadataFilterResponse,
    summary="Cascading metadata filter for dropdown values",
    tags=["Metadata"],
)
def metadata_filter(
    request: MetadataFilterRequest, db: Session = Depends(get_db)
):
    """
    Returns distinct metadata values for cascading dropdowns.

    - Multi-select supported on all fields.
    - Empty array = no filter (return all distinct values).
    - Uses IN semantics for multi-select.

    Example: selecting market=["India"] narrows down available regions/channels/etc.
    """
    return metadata_service.get_cascading_filters(db, request)
