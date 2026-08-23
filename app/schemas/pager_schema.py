"""
Pydantic v2 schemas for Pager.

IMPORTANT: field `retailer` is used (not `retailer`).
Fields: market, retailer, channel, category, campaign_focus
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

from app.utils.enums import ScoringMode, PagerStatus
from app.schemas.pillar_schema import PillarCreate, PillarUpdate, PillarOut


class PagerCreate(BaseModel):
    title: str
    market: Optional[str] = None
    retailer: Optional[str] = None
    channel: Optional[str] = None
    category: Optional[str] = None
    campaign_focus: Optional[str] = None
    business_outcome_statement: Optional[str] = None
    scoring_mode: ScoringMode = ScoringMode.UNWEIGHTED
    status: PagerStatus = PagerStatus.DRAFT
    track: Optional[str] = None
    pager_type: Optional[str] = None
    image_url: Optional[str] = None
    created_by: Optional[str] = None
    published_by: Optional[str] = None
    published_at: Optional[datetime] = None
    pillars: Optional[List[PillarCreate]] = Field(default_factory=list)


class PagerUpdate(BaseModel):
    """PATCH payload — all fields optional."""
    title: Optional[str] = None
    market: Optional[str] = None
    retailer: Optional[str] = None
    channel: Optional[str] = None
    category: Optional[str] = None
    campaign_focus: Optional[str] = None
    business_outcome_statement: Optional[str] = None
    scoring_mode: Optional[ScoringMode] = None
    status: Optional[PagerStatus] = None
    track: Optional[str] = None
    pager_type: Optional[str] = None
    image_url: Optional[str] = None
    updated_by: Optional[str] = None
    published_by: Optional[str] = None
    published_at: Optional[datetime] = None
    pillars: Optional[List[PillarUpdate]] = None


class StatusUpdate(BaseModel):
    status: PagerStatus
    updated_by: Optional[str] = None
    published_by: Optional[str] = None
    published_at: Optional[datetime] = None


class PagerOut(BaseModel):
    pager_id: str
    title: str
    market: Optional[str] = None
    retailer: Optional[str] = None
    channel: Optional[str] = None
    category: Optional[str] = None
    campaign_focus: Optional[str] = None
    business_outcome_statement: Optional[str] = None
    scoring_mode: ScoringMode
    status: PagerStatus
    track: Optional[str] = None
    pager_type: Optional[str] = None
    image_url: Optional[str] = None
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_by: Optional[str] = None
    updated_at: Optional[datetime] = None
    published_by: Optional[str] = None
    published_at: Optional[datetime] = None
    pillars: List[PillarOut] = []

    model_config = {"from_attributes": True}


class PagerSummary(BaseModel):
    """Pager record schema containing all pager table fields without pillars/initiatives."""
    pager_id: str
    title: str
    market: Optional[str] = None
    retailer: Optional[str] = None
    channel: Optional[str] = None
    category: Optional[str] = None
    campaign_focus: Optional[str] = None
    business_outcome_statement: Optional[str] = None
    scoring_mode: ScoringMode
    status: PagerStatus
    track: Optional[str] = None
    pager_type: Optional[str] = None
    image_url: Optional[str] = None
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_by: Optional[str] = None
    updated_at: Optional[datetime] = None
    published_by: Optional[str] = None
    published_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class FetchAllPagersRequest(BaseModel):
    """
    Multi-select filter request for fetch-all pagers.
    Empty list or null means no filter for that dimension.
    Status defaults to all non-DELETED pagers (DRAFT, PUBLISHED, ARCHIVED) if empty.
    """
    user_id: Optional[List[str]] = Field(default_factory=list)
    market: Optional[List[str]] = Field(default_factory=list)
    retailer: Optional[List[str]] = Field(default_factory=list)
    channel: Optional[List[str]] = Field(default_factory=list)
    category: Optional[List[str]] = Field(default_factory=list)
    campaign: Optional[List[str]] = Field(default_factory=list)
    campaign_focus: Optional[List[str]] = Field(default_factory=list)
    pager_type: Optional[List[str]] = Field(default_factory=list)
    status: Optional[List[str]] = Field(default_factory=list)


class FetchAllPagersResponse(BaseModel):
    total: int
    pagers: List[PagerSummary] = []
