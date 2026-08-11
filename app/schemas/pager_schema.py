"""
Pydantic v2 schemas for Pager.

IMPORTANT: field `region` is used (not `retailer`).
Fields: market, region, channel, category, campaign_focus
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

from app.utils.enums import ScoringMode, PagerStatus
from app.schemas.pillar_schema import PillarCreate, PillarUpdate, PillarOut


class PagerCreate(BaseModel):
    title: str
    market: Optional[str] = None
    region: Optional[str] = None
    channel: Optional[str] = None
    category: Optional[str] = None
    campaign_focus: Optional[str] = None
    business_outcome_statement: Optional[str] = None
    scoring_mode: ScoringMode = ScoringMode.UNWEIGHTED
    status: PagerStatus = PagerStatus.DRAFT
    track: Optional[str] = None
    pager_type: Optional[str] = None
    created_by: Optional[str] = None
    pillars: Optional[List[PillarCreate]] = Field(default_factory=list)


class PagerUpdate(BaseModel):
    """PATCH payload — all fields optional."""
    title: Optional[str] = None
    market: Optional[str] = None
    region: Optional[str] = None
    channel: Optional[str] = None
    category: Optional[str] = None
    campaign_focus: Optional[str] = None
    business_outcome_statement: Optional[str] = None
    scoring_mode: Optional[ScoringMode] = None
    track: Optional[str] = None
    pager_type: Optional[str] = None
    updated_by: Optional[str] = None
    pillars: Optional[List[PillarUpdate]] = None


class StatusUpdate(BaseModel):
    status: PagerStatus
    updated_by: Optional[str] = None


class PagerOut(BaseModel):
    pager_id: str
    title: str
    market: Optional[str] = None
    region: Optional[str] = None
    channel: Optional[str] = None
    category: Optional[str] = None
    campaign_focus: Optional[str] = None
    business_outcome_statement: Optional[str] = None
    scoring_mode: ScoringMode
    status: PagerStatus
    track: Optional[str] = None
    pager_type: Optional[str] = None
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_by: Optional[str] = None
    updated_at: Optional[datetime] = None
    published_by: Optional[str] = None
    published_at: Optional[datetime] = None
    pillars: List[PillarOut] = []

    model_config = {"from_attributes": True}


class PagerSummary(BaseModel):
    """Lightweight pager summary without full pillar tree."""
    pager_id: str
    title: str
    market: Optional[str] = None
    region: Optional[str] = None
    channel: Optional[str] = None
    category: Optional[str] = None
    campaign_focus: Optional[str] = None
    scoring_mode: ScoringMode
    status: PagerStatus
    pager_type: Optional[str] = None
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
