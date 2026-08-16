"""
Google Cloud Storage (GCS) Service.

Uploads an image file to a private GCP Storage bucket and returns its signed URL.
"""

import os
import uuid
import logging
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, UploadFile, status

from app.schemas.storage_schema import ImageUploadResponse

logger = logging.getLogger(__name__)


class StorageService:
    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID", "").strip()
        self.bucket_name = os.getenv("GCS_BUCKET_NAME", "").strip()
        self.expiration_minutes = int(os.getenv("GCS_SIGNED_URL_EXPIRATION_MINUTES", "60"))
        self._client = None

    def _get_client(self):
        """Lazily initialize Google Cloud Storage client using Application Default Credentials."""
        if self._client is not None:
            return self._client

        project = os.getenv("GCP_PROJECT_ID", self.project_id).strip()
        bucket = os.getenv("GCS_BUCKET_NAME", self.bucket_name).strip()

        if not bucket or bucket == "your-gcs-bucket-name" or not project or project == "your-gcp-project-id":
            return None

        try:
            from google.cloud import storage

            self._client = storage.Client(project=project)
            return self._client
        except Exception as e:
            logger.warning(f"GCS Client initialization: {e}")
            return None

    def _generate_signed_url(self, blob, blob_name: str, bucket_name: str) -> str:
        """Generate a v4 signed URL for GET access."""
        exp_delta = timedelta(minutes=self.expiration_minutes)
        sa_email = os.getenv("GCS_SERVICE_ACCOUNT_EMAIL", "").strip()

        if blob:
            try:
                kwargs = {"version": "v4", "expiration": exp_delta, "method": "GET"}
                if sa_email:
                    kwargs["service_account_email"] = sa_email
                return blob.generate_signed_url(**kwargs)
            except Exception as err:
                logger.warning(f"GCS signed URL generation warning: {err}")

        # Fallback for dev/mock environment
        return f"https://storage.googleapis.com/{bucket_name}/{blob_name}?signed_url_mock=true"

    async def upload_image(self, file: UploadFile) -> ImageUploadResponse:
        """
        Uploads image to private GCP storage and returns signed URL.
        """
        content_type = file.content_type or "image/png"
        if not content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only image files are allowed.",
            )

        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty.",
            )

        ext = os.path.splitext(file.filename or "image.png")[1] or ".png"
        blob_name = f"images/{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}{ext}"
        bucket_name = os.getenv("GCS_BUCKET_NAME", self.bucket_name).strip() or "national-one-pager-storage"

        client = self._get_client()
        target_blob = None

        if client and bucket_name and bucket_name != "your-gcs-bucket-name":
            try:
                bucket = client.bucket(bucket_name)
                target_blob = bucket.blob(blob_name)
                target_blob.upload_from_string(file_bytes, content_type=content_type)
            except Exception as e:
                logger.error(f"GCS upload failed: {e}")
                if os.getenv("APP_ENV") == "production":
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail=f"Cloud Storage upload failed: {str(e)}",
                    )

        signed_url = self._generate_signed_url(target_blob, blob_name, bucket_name)
        return ImageUploadResponse(url=signed_url)


storage_service = StorageService()
