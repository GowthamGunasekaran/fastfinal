from pydantic import BaseModel, Field, field_validator

Status = str
ScoringMode = str


class InitiativeIn(BaseModel):
    initiative_number: int = Field(ge=1, le=3)
    priority_level: str | None = None
    accountable_function_department: str | None = None
    initiative_description: str | None = None
    kpi_metric: str | None = None
    success_target: str | None = None
    unit: str | None = None
    week_start: str | None = None
    week_end: str | None = None
    guidelines: str | None = None
    checklist_compliance_notes: str | None = None
    image_urls: list[str] = Field(default_factory=list, max_length=3)

    @field_validator("image_urls")
    @classmethod
    def validate_image_count(cls, value):
        if len(value) > 3:
            raise ValueError("Maximum 3 image URLs are allowed per initiative.")
        return value


class InitiativeUpdate(InitiativeIn):
    initiative_id: str | None = None


class PillarIn(BaseModel):
    pillar_number: int = Field(ge=1, le=5)
    pillar_name: str | None = None
    pillar_description: str | None = None
    pillar_weight: float | None = Field(default=None, ge=0, le=100)
    initiatives: list[InitiativeIn] = Field(default_factory=list, max_length=3)

    @field_validator("initiatives")
    @classmethod
    def validate_initiatives(cls, value):
        numbers = [item.initiative_number for item in value]
        if len(numbers) != len(set(numbers)):
            raise ValueError("initiative_number must be unique within a pillar.")
        return value


class PillarUpdate(BaseModel):
    pillar_id: str | None = None
    pillar_number: int = Field(ge=1, le=5)
    pillar_name: str | None = None
    pillar_description: str | None = None
    pillar_weight: float | None = Field(default=None, ge=0, le=100)
    initiatives: list[InitiativeUpdate] = Field(default_factory=list, max_length=3)

    @field_validator("initiatives")
    @classmethod
    def validate_initiatives(cls, value):
        numbers = [item.initiative_number for item in value]
        if len(numbers) != len(set(numbers)):
            raise ValueError("initiative_number must be unique within a pillar.")
        return value


class StatusUpdate(BaseModel):
    status: str
    updated_by: str
