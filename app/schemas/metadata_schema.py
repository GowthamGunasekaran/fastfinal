"""
Pydantic v2 schemas for Metadata cascading filter API.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel


class MarketMetadataItem(BaseModel):
    """
    Metadata dimensions and campaigns for a single market.
    """
    retailer: List[str] = []
    channel: List[str] = []
    category: List[str] = []
    campaign: List[str] = []


class MetadataOut(BaseModel):
    metadata_id: int
    market: str
    retailer: List[str] = []
    channel: List[str] = []
    category: List[str] = []

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


# Type alias for dictionary response mapping market -> MarketMetadataItem
MetadataDictResponse = Dict[str, MarketMetadataItem]
