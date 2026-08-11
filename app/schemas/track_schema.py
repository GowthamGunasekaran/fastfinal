"""
Pydantic v2 schemas for the Update Track API.

PATCH /api/v1/update-track
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field, model_validator


class UpdateTrackRequest(BaseModel):
    """
    Request body for PATCH /api/v1/update-track.

    - table="pager"      → requires pager_id only.
    - table="pillar"     → requires pager_id + pillar_id.
    - table="initiative" → requires pager_id + pillar_id + initiative_id.
    """
    table: Literal["pager", "pillar", "initiative"]
    pager_id: str = Field(..., description="UUID of the Pager (always required)")
    pillar_id: Optional[str] = Field(None, description="UUID of the Pillar (required for pillar/initiative)")
    initiative_id: Optional[str] = Field(None, description="UUID of the Initiative (required for initiative)")
    track: str = Field(..., min_length=1, description="New track value (must not be empty)")
    updated_by: str = Field(..., min_length=1, description="User performing the update")

    @model_validator(mode="after")
    def validate_required_ids(self) -> "UpdateTrackRequest":
        if self.table == "pillar" and not self.pillar_id:
            raise ValueError("pillar_id is required when table is 'pillar'")
        if self.table == "initiative":
            if not self.pillar_id:
                raise ValueError("pillar_id is required when table is 'initiative'")
            if not self.initiative_id:
                raise ValueError("initiative_id is required when table is 'initiative'")
        return self


class UpdateTrackResponse(BaseModel):
    """Response body for a successful track update."""
    message: str = "Track updated successfully"
    table: str
    pager_id: str
    pillar_id: Optional[str] = None
    initiative_id: Optional[str] = None
    track: str
    updated_by: str
