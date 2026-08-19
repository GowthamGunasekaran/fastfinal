"""
Schema for Image Upload endpoint.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class ImageUploadResponse(BaseModel):
    urls: List[str] = Field(default_factory=list, description="Array of signed URLs of uploaded images")
    url: Optional[str] = Field(None, description="Primary signed URL of the uploaded image (for backwards compatibility)")

