"""
Pydantic v2 schemas for Metadata cascading filter API.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field, AliasChoices


class MarketMetadataItem(BaseModel):
    """
    Metadata dimensions and campaigns for a single market.
    """
    retailer: List[str] = []
    channel: List[str] = []
    category: List[str] = []
    campaign: List[str] = []
    accountable_team: List[str] = Field(default=[], validation_alias=AliasChoices("accountable_team", "accountable_table"))
    pillar_kpi_1: List[str] = []
    pillar_kpi_2: List[str] = []
    pillar_kpi_3: List[str] = []
    pillar_kpi_4: List[str] = []
    pillar_kpi_5: List[str] = []


class MetadataUpsertRequest(BaseModel):
    """
    Request payload to add or update metadata for a market.
    """
    market: str
    retailer: List[str] = []
    channel: List[str] = []
    category: List[str] = []
    campaign: List[str] = []
    accountable_team: List[str] = Field(default=[], validation_alias=AliasChoices("accountable_team", "accountable_table"))
    pillar_kpi_1: List[str] = []
    pillar_kpi_2: List[str] = []
    pillar_kpi_3: List[str] = []
    pillar_kpi_4: List[str] = []
    pillar_kpi_5: List[str] = []


class MetadataOut(BaseModel):
    metadata_id: int
    market: str
    retailer: List[str] = []
    channel: List[str] = []
    category: List[str] = []
    campaign: List[str] = []
    accountable_team: List[str] = Field(default=[], validation_alias=AliasChoices("accountable_team", "accountable_table"))
    pillar_kpi_1: List[str] = []
    pillar_kpi_2: List[str] = []
    pillar_kpi_3: List[str] = []
    pillar_kpi_4: List[str] = []
    pillar_kpi_5: List[str] = []

    model_config = {"from_attributes": True}


class MetadataFilterRequest(BaseModel):
    """
    Filter request. Empty market list or omitting market returns all markets.
    """
    market: Optional[List[str]] = []
    retailer: Optional[List[str]] = []
    channel: Optional[List[str]] = []
    category: Optional[List[str]] = []
    campaign: Optional[List[str]] = []
    pager_type: Optional[List[str]] = []
    status: Optional[List[str]] = []
    accountable_team: Optional[List[str]] = Field(default=[], validation_alias=AliasChoices("accountable_team", "accountable_table"))
    pillar_kpi_1: Optional[List[str]] = []
    pillar_kpi_2: Optional[List[str]] = []
    pillar_kpi_3: Optional[List[str]] = []
    pillar_kpi_4: Optional[List[str]] = []
    pillar_kpi_5: Optional[List[str]] = []


# Type alias for dictionary response mapping market -> MarketMetadataItem
MetadataDictResponse = Dict[str, MarketMetadataItem]

