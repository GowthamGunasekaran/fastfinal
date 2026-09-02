"""
Schema for Image Upload endpoint.
"""

from typing import List
from pydantic import BaseModel, Field


class ImageUploadItem(BaseModel):
    image_url: str = Field(..., description="public url to store the image path in db")
    image_signed_url: str = Field(..., description="signed url to display the image in ui")


# Alias for list response
ImageUploadResponse = List[ImageUploadItem]
