"""
Schema for Image Upload endpoint.
"""

from typing import List
from pydantic import BaseModel, Field


class ImageUploadItem(BaseModel):
    image_name: str = Field(..., description="Image blob name (e.g. images/xxx.png) to store in db")
    image_signed_url: str = Field(..., description="Signed url to display the image in UI")


# Alias for list response
ImageUploadResponse = List[ImageUploadItem]
