from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.pager_pillar_initiative_schema import (
    InitiativeIn,
    InitiativeUpdate,
    PillarIn,
    PillarUpdate,
)


class PagerCreate(BaseModel):
    market: str | None = None
    category: str | None = None
    campaign_focus: str | None = None
    channel: str | None = None
    title: str
    business_outcome_statement: str | None = None
    scoring_mode: str = "UNWEIGHTED"
    status: str = "DRAFT"
    created_by: str
    pillars: list[PillarIn] = Field(default_factory=list, max_length=5)

    @field_validator("pillars")
    @classmethod
    def validate_pillars(cls, value):
        numbers = [item.pillar_number for item in value]
        if len(numbers) != len(set(numbers)):
            raise ValueError("pillar_number must be unique within a pager.")
        return value


class PagerUpdate(BaseModel):
    market: str | None = None
    category: str | None = None
    campaign_focus: str | None = None
    channel: str | None = None
    title: str | None = None
    business_outcome_statement: str | None = None
    scoring_mode: str | None = None
    status: str | None = None
    updated_by: str
    pillars: list[PillarUpdate] | None = Field(default=None, max_length=5)

    @field_validator("pillars")
    @classmethod
    def validate_pillars(cls, value):
        if value is None:
            return value
        numbers = [item.pillar_number for item in value]
        if len(numbers) != len(set(numbers)):
            raise ValueError("pillar_number must be unique within a pager.")
        return value

class InitiativeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    pillar_initiative_id: int
    initiative_id: str
    initiative_number: int
    priority_level: str | None
    accountable_function_department: str | None
    initiative_description: str | None
    kpi_metric: str | None
    success_target: str | None
    unit: str | None
    week_start: str | None
    week_end: str | None
    guidelines: str | None
    checklist_compliance_notes: str | None
    image_urls: list[str]
    status: str
class PillarOut(BaseModel):
    pillar_id: str
    pillar_number: int
    pillar_name: str | None
    pillar_description: str | None
    pillar_weight: float | None
    initiatives: list[InitiativeOut]


class PagerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    pager_id: int
    market: str | None
    category: str | None
    campaign_focus: str | None
    channel: str | None
    title: str
    business_outcome_statement: str | None
    scoring_mode: str
    status: str
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: str
    pillars: list[PillarOut]


class UserPagerSummary(BaseModel):
    created_by: str
    total: int
    draft: int
    published: int
    deleted: int
    archived: int
    pagers: list[PagerOut]
