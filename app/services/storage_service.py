"""
Google Cloud Storage (GCS) Service.

Production service for uploading image files to GCP Cloud Storage
and returning public & signed URLs.
"""

import os
import uuid
import logging
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from fastapi import HTTPException, UploadFile, status

from app.schemas.storage_schema import ImageUploadItem

load_dotenv()

logger = logging.getLogger(__name__)


class StorageService:
    def __init__(self):
        self._client = None
        self.bucket_name = os.getenv("GCS_BUCKET_NAME", "").strip()
        self.project_id = os.getenv("GCP_PROJECT_ID", "").strip() or None
        self.timeout_seconds = int(os.getenv("GCS_TIMEOUT_SECONDS", "30"))

    def _get_client(self):
        """Initializes and returns the Google Cloud Storage client."""
        if self._client is not None:
            return self._client
        try:
            from google.cloud import storage

            if self.project_id:
                self._client = storage.Client(project=self.project_id)
            else:
                self._client = storage.Client()
            return self._client
        except Exception as e:
            logger.error(f"GCS client initialization failed: {e}")
            return None

    def _get_bucket(self):
        """Returns the connected GCS bucket instance, or None if unavailable."""
        client = self._get_client()
        if not client or not self.bucket_name:
            return None
        try:
            return client.bucket(self.bucket_name)
        except Exception as e:
            logger.error(f"Failed to access GCS bucket '{self.bucket_name}': {e}")
            return None

    def _generate_signed_url(self, blob, expiration_hours: int = 24) -> str:
        """
        Generates a v4 signed URL for an uploaded GCS blob.
        Supports both credentials with private key and GCP Cloud Run / GCE IAM signing.
        """
        if blob is None:
            return ""

        expiration = timedelta(hours=expiration_hours)

        # 1. Direct v4 signing (standard when credentials have signing capability or key)
        try:
            return blob.generate_signed_url(
                version="v4",
                expiration=expiration,
                method="GET",
            )
        except Exception as direct_err:
            logger.debug(f"Direct v4 signing failed: {direct_err}. Attempting IAM signing...")

        # 2. GCP Managed Environment (Cloud Run / GCE) using service account token from metadata
        try:
            client = self._get_client()
            creds = getattr(client, "_credentials", None)
            if creds:
                if not getattr(creds, "valid", False) or not getattr(creds, "token", None):
                    from google.auth.transport.requests import Request

                    creds.refresh(Request())

                access_token = getattr(creds, "token", None)
                sa_email = getattr(creds, "service_account_email", None)

                if not sa_email or sa_email == "default":
                    from google.auth.compute_engine import _metadata
                    from google.auth.transport.requests import Request

                    info = _metadata.get_service_account_info(Request(), service_account="default")
                    if info and "email" in info:
                        sa_email = info["email"]

                if sa_email and sa_email != "default" and access_token:
                    return blob.generate_signed_url(
                        version="v4",
                        expiration=expiration,
                        method="GET",
                        service_account_email=sa_email,
                        access_token=access_token,
                    )
        except Exception as iam_err:
            logger.warning(f"IAM signed URL generation failed: {iam_err}")

        return ""

    async def upload_images(self, files: List[UploadFile]) -> List[ImageUploadItem]:
        """
        Uploads image files (up to 3) to GCP Cloud Storage.
        For each file:
        1. Validates the file (image format, non-empty, max 3 files).
        2. Uploads the image into the GCS bucket.
        3. Generates a signed URL for the uploaded blob.
        4. Generates a public URL.
        5. Returns the items to the UI.
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

        is_testing = os.getenv("TESTING") == "1"
        bucket = self._get_bucket()

        # In production / non-test mode, verify bucket connection before proceeding
        if not bucket and not is_testing:
            logger.error("Cloud Storage bucket is not configured or connection failed.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Cloud Storage is not configured properly or unavailable.",
            )

        items: List[ImageUploadItem] = []

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

            signed_url = ""
            if bucket:
                try:
                    target_blob = bucket.blob(blob_name)
                    # Upload the image into the GCS bucket
                    target_blob.upload_from_string(
                        file_bytes,
                        content_type=content_type,
                        timeout=self.timeout_seconds,
                    )
                    # After upload, generate the signed URL
                    signed_url = self._generate_signed_url(target_blob, expiration_hours=24)
                except Exception as e:
                    logger.error(f"GCS upload failed for file {file.filename}: {e}")
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail=f"Cloud Storage upload failed for file {file.filename}: {e}",
                    )

            bucket_name = self.bucket_name or "storage"
            public_url = f"https://storage.googleapis.com/{bucket_name}/{blob_name}"

            items.append(
                ImageUploadItem(
                    image_url=public_url,
                    image_signed_url=signed_url or "",
                )
            )

        return items

    async def upload_image(self, file: UploadFile) -> List[ImageUploadItem]:
        """Uploads a single image file (backwards compatibility)."""
        return await self.upload_images([file])

    def get_signed_url_from_public_url(
        self, public_url: Optional[str], expiration_hours: int = 24
    ) -> str:
        """
        Extracts blob name from public URL and returns a 24-hour signed URL.
        Returns empty string if signing is not available or fails.
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

            bucket_name = self.bucket_name
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

            if not blob_name or not bucket_name:
                return ""

            client = self._get_client()
            if client:
                bucket = client.bucket(bucket_name)
                blob = bucket.blob(blob_name)
                return self._generate_signed_url(blob, expiration_hours=expiration_hours)

            return ""
        except Exception as e:
            logger.warning(f"Error generating signed URL from public URL '{url_str}': {e}")
            return ""


storage_service = StorageService()


def get_signed_url_from_public_url(
    public_url: Optional[str], expiration_hours: int = 24
) -> str:
    """Common function to generate a signed URL from an existing public GCS URL."""
    return storage_service.get_signed_url_from_public_url(
        public_url, expiration_hours=expiration_hours
    )
