"""
Pydantic v2 schemas for Campaign.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, model_validator


class CampaignCreate(BaseModel):
    market: str
    campaign_name: str
    created_by: Optional[str] = None
    user_id: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def populate_fields(cls, data):
        if isinstance(data, dict):
            # Allow 'campaign' as alias for 'campaign_name'
            if "campaign" in data and "campaign_name" not in data:
                data["campaign_name"] = data["campaign"]
            # Allow 'user_id' as alias for 'created_by'
            if "user_id" in data and not data.get("created_by"):
                data["created_by"] = data["user_id"]
            elif "created_by" in data and not data.get("user_id"):
                data["user_id"] = data["created_by"]
        return data


class CampaignOut(BaseModel):
    campaign_id: str
    market: str
    campaign_name: str
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class CampaignListResponse(BaseModel):
    total: int
    campaigns: List[CampaignOut] = []
