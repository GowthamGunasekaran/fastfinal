"""
Google Cloud Storage (GCS) Service.

Uploads image files to a GCP Storage bucket and returns public URLs.
Designed for Cloud Run deployment using native Application Default Credentials (ADC).
Supports single or multiple file uploads (array of files, up to 3 files).
"""

import os
import uuid
import logging
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, UploadFile, status

from app.schemas.storage_schema import ImageUploadItem, ImageUploadResponse

logger = logging.getLogger(__name__)


class StorageService:
    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID", "").strip()
        self.bucket_name = os.getenv("GCS_BUCKET_NAME", "").strip()
        self.timeout_seconds = int(os.getenv("GCS_TIMEOUT_SECONDS", "30"))
        self._client = None

    def _get_client(self):
        """
        Lazily initialize Google Cloud Storage client using Application Default Credentials (ADC),
        which automatically binds to the Cloud Run service identity without needing JSON key files.
        """
        if self._client is not None:
            return self._client

        project = os.getenv("GCP_PROJECT_ID", self.project_id).strip()
        bucket = os.getenv("GCS_BUCKET_NAME", self.bucket_name).strip()

        if not bucket or bucket == "your-gcs-bucket-name":
            return None

        try:
            from google.cloud import storage

            kwargs = {}
            if project and project != "your-gcp-project-id":
                kwargs["project"] = project

            # Initializes using ADC (Application Default Credentials)
            self._client = storage.Client(**kwargs)
            return self._client
        except Exception as e:
            logger.warning(f"GCS Client initialization failed: {e}")
            return None

    def _generate_public_url(self, blob_name: str, bucket_name: str) -> str:
        """Generate standard public GCS URL for uploaded object."""
        return f"https://storage.googleapis.com/{bucket_name}/{blob_name}"

    async def upload_images(self, files: List[UploadFile]) -> List[ImageUploadItem]:
        """
        Uploads an array of image files (up to 3 files) to GCP Storage and returns array of objects with public and signed URLs.
        """
        if not files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No files provided for upload.",
            )

        if len(files) > 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum of 3 image files can be uploaded at a time.",
            )

        items: List[ImageUploadItem] = []
        bucket_name = os.getenv("GCS_BUCKET_NAME", self.bucket_name).strip() or "national-one-pager-storage"
        client = self._get_client()

        for index, file in enumerate(files):
            content_type = file.content_type or "image/png"
            if not content_type.startswith("image/"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File {index + 1} ({file.filename}) is not an image file.",
                )

            file_bytes = await file.read()
            if not file_bytes:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File {index + 1} ({file.filename}) is empty.",
                )

            ext = os.path.splitext(file.filename or "image.png")[1] or ".png"
            blob_name = f"images/{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}_{index + 1}{ext}"

            signed_url = None
            if client and bucket_name and bucket_name != "your-gcs-bucket-name":
                try:
                    bucket = client.bucket(bucket_name)
                    target_blob = bucket.blob(blob_name)
                    target_blob.upload_from_string(
                        file_bytes,
                        content_type=content_type,
                        timeout=self.timeout_seconds,
                    )
                    try:
                        signed_url = target_blob.generate_signed_url(
                            version="v4",
                            expiration=timedelta(hours=24),
                            method="GET",
                        )
                    except Exception as sign_err:
                        logger.warning(f"Failed to generate v4 signed URL: {sign_err}")
                        try:
                            signed_url = target_blob.generate_signed_url(
                                expiration=timedelta(hours=24),
                                method="GET",
                            )
                        except Exception:
                            signed_url = None
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"GCS upload failed for file {file.filename}: {error_msg}")
                    if os.getenv("APP_ENV") == "production":
                        raise HTTPException(
                            status_code=status.HTTP_502_BAD_GATEWAY,
                            detail=f"Cloud Storage upload failed for file {file.filename}: {error_msg}",
                        )

            public_url = self._generate_public_url(blob_name, bucket_name)
            items.append(
                ImageUploadItem(
                    image_url=public_url,
                    image_signed_url=signed_url or "",
                )
            )

        return items

    async def upload_image(self, file: UploadFile) -> List[ImageUploadItem]:
        """
        Uploads a single image file to GCP Storage and returns array of objects with public and signed URLs.
        """
        return await self.upload_images([file])

    def get_signed_url_from_public_url(
        self, public_url: Optional[str], expiration_hours: int = 24
    ) -> str:
        """
        Takes a public GCS URL, extracts the bucket and blob (image name),
        and generates a signed URL with 24-hour expiration.
        Returns empty string ("") if signing is not available or fails.
        """
        if not public_url:
            return ""

        url_str = str(public_url).strip()
        if not url_str:
            return ""

        try:
            from urllib.parse import urlparse, unquote

            parsed = urlparse(url_str)
            path = unquote(parsed.path.lstrip("/"))

            bucket_name = (
                os.getenv("GCS_BUCKET_NAME", self.bucket_name).strip()
                or "national-one-pager-storage"
            )
            blob_name = None

            if "storage.googleapis.com" in parsed.netloc:
                if parsed.netloc == "storage.googleapis.com":
                    parts = path.split("/", 1)
                    if len(parts) == 2:
                        bucket_name = parts[0]
                        blob_name = parts[1]
                    else:
                        blob_name = path
                else:
                    subdomain = parsed.netloc.replace(".storage.googleapis.com", "")
                    if subdomain:
                        bucket_name = subdomain
                    blob_name = path
            else:
                blob_name = path

            if not blob_name:
                return ""

            client = self._get_client()
            if client and bucket_name and bucket_name != "your-gcs-bucket-name":
                try:
                    bucket = client.bucket(bucket_name)
                    blob = bucket.blob(blob_name)
                    try:
                        return blob.generate_signed_url(
                            version="v4",
                            expiration=timedelta(hours=expiration_hours),
                            method="GET",
                        )
                    except Exception as sign_err:
                        logger.warning(
                            f"Failed to generate v4 signed URL for {blob_name}: {sign_err}"
                        )
                        try:
                            return blob.generate_signed_url(
                                expiration=timedelta(hours=expiration_hours),
                                method="GET",
                            )
                        except Exception:
                            return ""
                except Exception as e:
                    logger.warning(
                        f"Failed to access bucket {bucket_name} for signed URL: {e}"
                    )
                    return ""

            return ""
        except Exception as e:
            logger.warning(
                f"Error generating signed URL from public URL '{url_str}': {e}"
            )
            return ""


storage_service = StorageService()


def get_signed_url_from_public_url(
    public_url: Optional[str], expiration_hours: int = 24
) -> str:
    """
    Common function to extract image name from public URL, connect to bucket,
    and return a signed URL with 24-hour expiration, or empty string if not available.
    """
    return storage_service.get_signed_url_from_public_url(
        public_url, expiration_hours=expiration_hours
    )
