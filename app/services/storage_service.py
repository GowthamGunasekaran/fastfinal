"""
Google Cloud Storage (GCS) Service.

Production service for uploading image files to GCP Cloud Storage
and returning public & signed URLs using IAM SignBlob.
"""

import os
import uuid
import logging
from typing import List, Optional
from datetime import timedelta
from dotenv import load_dotenv
from fastapi import HTTPException, UploadFile, status
from google.cloud import storage
import google.auth
from google.auth.transport.requests import Request

from app.schemas.storage_schema import ImageUploadItem

load_dotenv()

logger = logging.getLogger(__name__)


class StorageService:
    def __init__(
        self,
        bucket_name: Optional[str] = None,
        project_id: Optional[str] = None,
    ):
        self.project_id = project_id or os.environ.get("GCP_PROJECT_ID")
        self.bucket_name = bucket_name or os.environ.get("GCS_BUCKET_NAME")
        self.service_account_email = (
            os.environ.get("SERVICE_ACCOUNT_EMAIL")
            or os.environ.get("GCS_SERVICE_ACCOUNT_EMAIL")
        )
        self.client: Optional[storage.Client] = None
        self.bucket = None
        self.credentials = None
        self._request = Request()
        self._initialized = False

    def initialize_connection(self):
        """
        Establishes and caches the GCP Storage client, bucket connection,
        and auth credentials globally so subsequent calls don't incur connection overhead.
        """
        if self._initialized:
            return
        self._initialized = True
        try:
            if self.project_id:
                self.client = storage.Client(project=self.project_id)
            else:
                self.client = storage.Client()

            if self.bucket_name:
                self.bucket = self.client.bucket(self.bucket_name)

            self.credentials, _ = google.auth.default(
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
            logger.info("GCP Storage global connection and credentials initialized.")
        except Exception as e:
            logger.warning(f"GCP Storage initialization warning: {e}")

    def _get_client(self):
        """Returns the active GCS client, reconnecting if needed."""
        if not self._initialized:
            self.initialize_connection()
        return self.client

    def _get_bucket(self, bucket_name: Optional[str] = None):
        """Returns the pre-established bucket connection, or connects to the specified bucket."""
        target_bucket = bucket_name or self.bucket_name
        if not target_bucket:
            return None
        if self.bucket and self.bucket_name == target_bucket:
            return self.bucket
        client = self._get_client()
        return client.bucket(target_bucket) if client else None

    def _get_credentials_token(self) -> Optional[str]:
        """
        Refreshes and returns the GCP access token.
        Token is valid for 1 hour; only refreshes when expired to prevent latency.
        """
        if not self.service_account_email:
            return None

        try:
            if self.credentials is None:
                self.credentials, _ = google.auth.default(
                    scopes=["https://www.googleapis.com/auth/cloud-platform"]
                )
            if not getattr(self.credentials, "valid", False) or not getattr(self.credentials, "token", None):
                self.credentials.refresh(self._request)
            return self.credentials.token
        except Exception as e:
            logger.warning(f"Could not refresh GCP credentials token: {e}")
            return None

    def generate_signed_url(
        self,
        bucket_name: str,
        blob_name: str,
        expiration: timedelta = timedelta(minutes=15),
    ) -> str:
        """
        Generates a v4 signed URL for a GCS blob via IAM SignBlob.
        Reuses the pre-established global bucket connection and cached credentials for maximum speed.
        """
        try:
            bucket = self._get_bucket(bucket_name)
            if not bucket:
                return ""
            blob = bucket.blob(blob_name)

            sa_email = self.service_account_email
            if sa_email:
                token = self._get_credentials_token()
                if token:
                    return blob.generate_signed_url(
                        version="v4",
                        expiration=expiration,
                        method="GET",
                        service_account_email=sa_email,
                        access_token=token,
                    )

            # Fallback for local / standard credentials
            return blob.generate_signed_url(
                version="v4",
                expiration=expiration,
                method="GET",
            )
        except Exception as e:
            logger.warning(f"Signed URL generation failed for {blob_name}: {e}")
            return ""

    async def upload_images(self, files: List[UploadFile]) -> List[ImageUploadItem]:
        """
        Uploads image files directly into the GCP bucket and returns public & signed URLs.
        """
        if not files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file selected",
            )

        if len(files) > 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum of 3 image files can be uploaded at a time.",
            )

        bucket = self._get_bucket()
        if not bucket:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="GCP Storage bucket connection is not available.",
            )

        items: List[ImageUploadItem] = []

        for index, file in enumerate(files):
            if not file.filename:
                raise HTTPException(status_code=400, detail="No file selected")

            content_type = file.content_type or "image/png"
            if not content_type.startswith("image/"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File {index + 1} ({file.filename}) is not an image file.",
                )

            contents = await file.read()
            if not contents:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File {index + 1} ({file.filename}) is empty.",
                )

            ext = os.path.splitext(file.filename)[1] or ".png"
            blob_name = f"images/{uuid.uuid4().hex}{ext}"

            try:
                blob = bucket.blob(blob_name)
                blob.upload_from_string(contents, content_type=content_type)
                signed_url = self.generate_signed_url(self.bucket_name, blob_name)
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"GCS upload failed for file {file.filename}: {e}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Cloud Storage upload failed for file {file.filename}: {e}",
                )

            items.append(
                ImageUploadItem(
                    image_name=blob_name,
                    image_signed_url=signed_url,
                )
            )

        return items

    async def upload_image(self, file: UploadFile) -> List[ImageUploadItem]:
        """Uploads a single image file (backwards compatibility)."""
        return await self.upload_images([file])

    def get_signed_url(
        self,
        image_name: Optional[str],
        expiration_hours: int = 24,
    ) -> str:
        """
        Generates a signed URL directly from an image/blob name (e.g. 'images/abc.png').
        """
        if not image_name:
            return ""

        clean_name = str(image_name).strip()
        if not clean_name:
            return ""

        return self.generate_signed_url(
            bucket_name=self.bucket_name or "",
            blob_name=clean_name,
            expiration=timedelta(hours=expiration_hours),
        )


storage_service = StorageService()


def generate_signed_url(bucket_name: str, blob_name: str) -> str:
    """Convenience function matching the signature in Image 1."""
    return storage_service.generate_signed_url(bucket_name, blob_name)


def get_signed_url(
    image_name: Optional[str], expiration_hours: int = 24
) -> str:
    """Convenience function to generate signed URL directly from image name."""
    return storage_service.get_signed_url(
        image_name, expiration_hours=expiration_hours
    )


GCPStorageService = StorageService

