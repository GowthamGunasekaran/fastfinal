"""
API v1 router — all routes registered here and included in main.py.
"""

from fastapi import APIRouter, Depends, Query, File, UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List, Dict

from app.db import get_db
from app.schemas.pager_schema import (
    PagerCreate,
    PagerUpdate,
    PagerOut,
    PagerSummary,
    StatusUpdate,
    FetchAllPagersRequest,
    FetchAllPagersResponse,
)
from app.schemas.metadata_schema import (
    MetadataFilterRequest,
    MarketMetadataItem,
    MetadataUpsertRequest,
    MetadataOut,
)
from app.schemas.track_schema import UpdateTrackRequest, UpdateTrackResponse
from app.schemas.campaign_schema import CampaignCreate, CampaignOut, CampaignListResponse
from app.schemas.storage_schema import ImageUploadItem, ImageUploadResponse
from app.schemas.pager_log_schema import PagerLogOut
from app.services.pager_service import pager_service
from app.services.metadata_service import metadata_service
from app.services.track_service import track_service
from app.services.campaign_service import campaign_service
from app.services.storage_service import storage_service
from app.services.pager_log_service import pager_log_service
from app.schemas.user_tracking_schema import (
    LoginLogCreate,
    LoginLogOut,
    ActionLogCreate,
    ActionLogOut,
    UserDetailsOut,
    UserDetailsUploadResponse,
)
from app.services.user_tracking_service import user_tracking_service
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


@router.post(
    "/pagers/fetch-all",
    response_model=FetchAllPagersResponse,
    summary="Fetch all pagers (only pager table records, excluding DELETED by default)",
    tags=["Pagers"],
)
def fetch_all_pagers_post(
    filters: Optional[FetchAllPagersRequest] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """
    Fetch all pager table records matching the JSON filter payload.
    Returns only pager table records (no pillars or initiatives).
    Excludes DELETED pagers by default (returns DRAFT, PUBLISHED, ARCHIVED).
    """
    if filters is None:
        filters = FetchAllPagersRequest()
    return pager_service.fetch_all_pagers(db, filters, skip=skip, limit=limit)


@router.get(
    "/pagers/{pager_id}",
    response_model=PagerOut,
    summary="Get Pager",
    tags=["Pagers"],
)
def get_pager(pager_id: str, db: Session = Depends(get_db)):
    return pager_service.get_pager(db, pager_id)


@router.put(
    "/pagers/{pager_id}",
    response_model=PagerOut,
    summary="Update Pager",
    tags=["Pagers"],
)
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
    Update / Partial update for a Pager.

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
    summary="Update Pager Status",
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
        db,
        pager_id,
        payload.status,
        updated_by=payload.updated_by,
        published_by=payload.published_by,
        published_at=payload.published_at,
    )


# ==========================================================================
# METADATA CASCADING ENDPOINT
# ==========================================================================

@router.post(
    "/metadata/filter",
    response_model=Dict[str, MarketMetadataItem],
    summary="Filter Metadata",
    tags=["Pagers"],
)
def metadata_filter(
    request: Optional[MetadataFilterRequest] = None, db: Session = Depends(get_db)
):
    """
    Returns market-keyed dictionary containing arrays of strings for
    retailer, channel, category, and campaign.
    """
    return metadata_service.get_cascading_filters(db, request)


@router.get(
    "/metadata",
    response_model=Dict[str, MarketMetadataItem],
    summary="Fetch All Metadata",
    tags=["Pagers"],
)
def fetch_metadata(db: Session = Depends(get_db)):
    """
    Fetch all metadata grouped by market as a dictionary mapping each market
    to its retailer, channel, category, and campaign string arrays.
    """
    return metadata_service.get_cascading_filters(db, MetadataFilterRequest())


@router.post(
    "/metadata",
    response_model=MetadataOut,
    summary="Add or Update Metadata for a Market",
    tags=["Pagers"],
)
def upsert_metadata(
    payload: MetadataUpsertRequest, db: Session = Depends(get_db)
):
    """
    Add or update metadata for a market.
    Accepts market, retailer, channel, category arrays (no campaigns).
    If the market exists, updates arrays; otherwise creates a new market record.
    """
    return metadata_service.upsert_metadata(db, payload)


# ==========================================================================
# UPDATE TRACK ENDPOINT
# ==========================================================================

@router.patch(
    "/update-track",
    response_model=UpdateTrackResponse,
    summary="Update track for a Pager, Pillar, or Initiative",
    tags=["Track"],
)
def update_track(payload: UpdateTrackRequest, db: Session = Depends(get_db)):
    """
    Update the `track` field for exactly one hierarchy level.

    - **table="pager"**       → updates `pager.track`      (requires pager_id)
    - **table="pillar"**      → updates `pillar.pillar_track`  (requires pager_id + pillar_id)
    - **table="initiative"**  → updates `initiative.initiative_track`  (requires pager_id + pillar_id + initiative_id)

    The full parent hierarchy is always validated — a pillar must belong to the
    specified pager, and an initiative must belong to the specified pager AND pillar.
    """
    return track_service.update_track(db, payload)


# ==========================================================================
# CAMPAIGN ENDPOINTS
# ==========================================================================

@router.post(
    "/campaigns",
    response_model=CampaignOut,
    status_code=201,
    summary="Create a new Campaign",
    tags=["Campaigns"],
)
@router.post(
    "/campaign",
    response_model=CampaignOut,
    status_code=201,
    include_in_schema=False,
)
def create_campaign(
    payload: CampaignCreate, db: Session = Depends(get_db)
):
    """
    Create a new Campaign record with market, campaign_name, and user_id (created_by).
    """
    return campaign_service.create_campaign(db, payload)


@router.get(
    "/campaigns",
    response_model=CampaignListResponse,
    summary="List Campaigns",
    tags=["Campaigns"],
)
@router.get(
    "/campaign",
    response_model=CampaignListResponse,
    include_in_schema=False,
)
def list_campaigns(
    market: Optional[List[str]] = Query(None, description="Filter by market(s)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """
    List campaigns with optional market filter.
    """
    return campaign_service.list_campaigns(db, market=market, skip=skip, limit=limit)


# ==========================================================================
# STORAGE / IMAGE UPLOAD (Single / Batch API)
# ==========================================================================

@router.post(
    "/upload",
    response_model=List[ImageUploadItem],
    status_code=status.HTTP_201_CREATED,
    summary="Upload image(s) to GCP Cloud Storage and get image names and signed URLs (up to 3 files)",
    tags=["Upload"],
)
async def upload_images(
    files: Optional[List[UploadFile]] = File(None, description="Array of image files to upload (up to 3 files)"),
    file: Optional[UploadFile] = File(None, description="Single image file to upload (backwards compatibility)"),
):
    """
    Upload image(s) to GCP Cloud Storage and return an array of image names and signed URLs.
    Accepts up to 3 image files in a single request.
    """
    upload_list: List[UploadFile] = []
    if files:
        upload_list.extend(files)
    if file:
        upload_list.append(file)

    if not upload_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files provided for upload.",
        )

    return await storage_service.upload_images(files=upload_list)


# ==========================================================================
# PAGER LOGS ENDPOINT
# ==========================================================================

@router.get(
    "/pager-logs",
    response_model=List[PagerLogOut],
    summary="Get audit logs for a user by email",
    tags=["Pager Logs"],
)
def get_pager_logs(
    email: str = Query(..., description="Email / user ID to fetch logs for"),
    limit: int = Query(10, ge=1, le=500, description="Number of recent logs to return (default 10)"),
    db: Session = Depends(get_db),
):
    """
    Fetch pager audit logs for a specific user (email).

    Matches rows where `created_by` OR `last_updated_by` equals the given email.
    Results are ordered by most recent first.
    - **email**: required — the user's email / ID.
    - **limit**: optional, default 10, max 500.
    """
    return pager_log_service.get_logs_by_email(db, email=email, limit=limit)


# ==========================================================================
# USER TRACKING ENDPOINTS
# ==========================================================================

@router.post(
    "/user-tracking/login-log",
    response_model=LoginLogOut,
    summary="Record a user login event",
    tags=["User Tracking"],
)
def record_login_log(payload: LoginLogCreate, db: Session = Depends(get_db)):
    """
    Record a user login event into `login_log`.
    Auto-populates GUID `id` and `login_time`.
    """
    return user_tracking_service.record_login(db, payload)


@router.post(
    "/user-tracking/action-log",
    response_model=ActionLogOut,
    summary="Record a user action event",
    tags=["User Tracking"],
)
def record_action_log(payload: ActionLogCreate, db: Session = Depends(get_db)):
    """
    Record an action event into `action_log`.
    Action can be VIEW, EXPORT, DRAFT, TRACK, or any free text.
    Auto-populates GUID `id` and `date_time`.
    """
    return user_tracking_service.record_action(db, payload)


@router.post(
    "/user-tracking/user-details/upload-csv",
    response_model=UserDetailsUploadResponse,
    summary="Upload and upsert user profiles via CSV file",
    tags=["User Tracking"],
)
async def upload_user_details_csv(
    file: UploadFile = File(..., description="CSV file containing email_id, role, and market"),
    db: Session = Depends(get_db),
):
    """
    Upload a CSV file containing user details (`email_id` / `email`, `role`, `market`).
    Performs upsert:
    - Inserts new user if email does not exist.
    - Updates role, market, and `last_updated_at` if email already exists.
    """
    return await user_tracking_service.upload_user_details_csv(db, file)


@router.get(
    "/user-tracking/user-details",
    response_model=UserDetailsOut,
    summary="Get user details by email",
    tags=["User Tracking"],
)
def get_user_details(
    email: str = Query(..., description="Email address of the user"),
    db: Session = Depends(get_db),
):
    """
    Fetch user details (email, role, market, created_at, last_updated_at)
    by email.
    """
    return user_tracking_service.get_user_details(db, email=email)



