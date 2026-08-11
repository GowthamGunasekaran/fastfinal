"""
Pydantic v2 schemas for Metadata cascading filter API.
"""

from typing import List, Optional
from pydantic import BaseModel


class MetadataOut(BaseModel):
    metadata_id: int
    market: str
    retailer: str
    channel: str
    category: str
    campaign: str

    model_config = {"from_attributes": True}


class MetadataFilterRequest(BaseModel):
    """
    Multi-select cascading filter request.
    Empty list means no filter (return all distinct values).
    """
    market: Optional[List[str]] = []
    retailer: Optional[List[str]] = []
    channel: Optional[List[str]] = []
    category: Optional[List[str]] = []
    campaign: Optional[List[str]] = []
    pager_type: Optional[List[str]] = []
    status: Optional[List[str]] = []


class MetadataFilterResponse(BaseModel):
    """
    Returns distinct available values for each dimension
    based on the selected filters (cascading behavior).
    """
    market: List[str] = []
    retailer: List[str] = []
    channel: List[str] = []
    category: List[str] = []
    campaign: List[str] = []
    pager_type: List[str] = []
    status: List[str] = []
