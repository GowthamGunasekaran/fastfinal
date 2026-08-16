"""
Schema for Image Upload endpoint.
"""

from pydantic import BaseModel, Field


class ImageUploadResponse(BaseModel):
    url: str = Field(..., description="Signed URL of the uploaded private GCP image")
