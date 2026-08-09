from pydantic import BaseModel, Field


class MetadataFilterRequest(BaseModel):
    market: list[str] = Field(default_factory=list)
    retailer: list[str] = Field(default_factory=list)
    channel: list[str] = Field(default_factory=list)
    category: list[str] = Field(default_factory=list)
    campaign: list[str] = Field(default_factory=list)


class MetadataFilterResponse(BaseModel):
    market: list[str]
    retailer: list[str]
    channel: list[str]
    category: list[str]
    campaign: list[str]