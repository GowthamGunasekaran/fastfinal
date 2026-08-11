"""
Pydantic v2 schemas for Pillar.
"""

from typing import List, Optional
from pydantic import BaseModel, Field

from app.schemas.initiative_schema import InitiativeCreate, InitiativeUpdate, InitiativeOut


class PillarCreate(BaseModel):
    pillar_number: int = Field(..., ge=1, le=5)
    pillar_name: Optional[str] = None
    pillar_description: Optional[str] = None
    pillar_weight: Optional[float] = None
    pillar_track: Optional[str] = None
    initiatives: Optional[List[InitiativeCreate]] = Field(default_factory=list)


class PillarUpdate(BaseModel):
    """Used for patching an existing pillar."""
    pillar_id: Optional[str] = None  # UUID — if provided, identifies existing pillar
    pillar_number: Optional[int] = Field(None, ge=1, le=5)
    pillar_name: Optional[str] = None
    pillar_description: Optional[str] = None
    pillar_weight: Optional[float] = None
    pillar_track: Optional[str] = None
    initiatives: Optional[List[InitiativeUpdate]] = None


class PillarOut(BaseModel):
    pillar_id: str
    pager_id: str
    pillar_number: int
    pillar_name: Optional[str] = None
    pillar_description: Optional[str] = None
    pillar_weight: Optional[float] = None
    pillar_track: Optional[str] = None
    initiatives: List[InitiativeOut] = []

    model_config = {"from_attributes": True}
