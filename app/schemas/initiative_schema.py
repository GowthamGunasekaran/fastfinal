"""
Pydantic v2 schemas for PillarInitiative (Initiative).

IMPORTANT: pillar_initiative_id is an INTEGER, not a string.
initiative_id is a UUID string.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class InitiativeCreate(BaseModel):
    initiative_number: int = Field(..., ge=1, le=3)
    initiative_track: Optional[str] = None
    priority_level: Optional[str] = None
    accountable_function_department: Optional[str] = None
    initiative_description: Optional[str] = None
    kpi_metric: Optional[str] = None
    success_target: Optional[str] = None
    unit: Optional[str] = None
    week_start: Optional[str] = None
    week_end: Optional[str] = None
    guidelines: Optional[str] = None
    checklist_compliance_notes: Optional[str] = None
    image_urls: Optional[List[str]] = Field(default_factory=list)

    @field_validator("image_urls")
    @classmethod
    def validate_image_count(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v and len(v) > 3:
            raise ValueError("Maximum 3 image URLs allowed per initiative.")
        return v


class InitiativeUpdate(BaseModel):
    """Used for patching an existing initiative."""
    initiative_id: Optional[str] = None  # UUID — if provided, identifies existing
    initiative_number: Optional[int] = Field(None, ge=1, le=3)
    initiative_track: Optional[str] = None
    priority_level: Optional[str] = None
    accountable_function_department: Optional[str] = None
    initiative_description: Optional[str] = None
    kpi_metric: Optional[str] = None
    success_target: Optional[str] = None
    unit: Optional[str] = None
    week_start: Optional[str] = None
    week_end: Optional[str] = None
    guidelines: Optional[str] = None
    checklist_compliance_notes: Optional[str] = None
    image_urls: Optional[List[str]] = None

    @field_validator("image_urls")
    @classmethod
    def validate_image_count(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v and len(v) > 3:
            raise ValueError("Maximum 3 image URLs allowed per initiative.")
        return v


class InitiativeOut(BaseModel):
    """API response schema for an initiative."""
    pillar_initiative_id: int  # INTEGER — not string
    initiative_id: str
    pager_id: str
    pillar_id: str
    initiative_number: int
    initiative_track: Optional[str] = None
    priority_level: Optional[str] = None
    accountable_function_department: Optional[str] = None
    initiative_description: Optional[str] = None
    kpi_metric: Optional[str] = None
    success_target: Optional[str] = None
    unit: Optional[str] = None
    week_start: Optional[str] = None
    week_end: Optional[str] = None
    guidelines: Optional[str] = None
    checklist_compliance_notes: Optional[str] = None
    image_urls: Optional[List[str]] = None

    model_config = {"from_attributes": True}
