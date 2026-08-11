"""
Pydantic v2 schemas for the Landing Page API.

Landing page only returns PUBLISHED pagers.
Supports multi-select filtering on market, region, channel, category, campaign.
"""

from typing import List, Optional
from pydantic import BaseModel

from app.schemas.pager_schema import PagerOut


class LandingPageFilterRequest(BaseModel):
    """
    Multi-select filter for the landing page.
    Empty list means no filter (return all published pagers).
    """
    market: Optional[List[str]] = []
    region: Optional[List[str]] = []
    channel: Optional[List[str]] = []
    category: Optional[List[str]] = []
    campaign_focus: Optional[List[str]] = []
    pager_type: Optional[List[str]] = []


class LandingPageResponse(BaseModel):
    total: int
    pagers: List[PagerOut] = []
