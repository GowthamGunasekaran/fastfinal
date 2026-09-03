"""
Google Cloud Storage (GCS) Service.

Uploads image files to a GCP Storage bucket and returns public & signed URLs.
Supports single or multiple file uploads (array of files, up to 3 files).
Authentication is loaded automatically from GOOGLE_APPLICATION_CREDENTIALS or native GCP ADC.
"""

import os
import uuid
import logging
from typing import List, Optional, Tuple
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from fastapi import HTTPException, UploadFile, status

from app.schemas.storage_schema import ImageUploadItem, ImageUploadResponse

load_dotenv()

logger = logging.getLogger(__name__)

PLACEHOLDER_BUCKETS = {"your-gcs-bucket-name", "your-bucket-name", ""}
PLACEHOLDER_PROJECTS = {"your-gcp-project-id", "your-project-id", ""}


class StorageService:
    def __init__(self):
        self._client = None
        self.timeout_seconds = int(os.getenv("GCS_TIMEOUT_SECONDS", "30"))

    def _get_configured_bucket(self) -> Optional[str]:
        """Returns the configured GCS bucket name, ignoring placeholder values."""
        bucket = os.getenv("GCS_BUCKET_NAME", "").strip()
        if not bucket or bucket in PLACEHOLDER_BUCKETS:
            return None
        return bucket

    def _get_configured_project(self) -> Optional[str]:
        """Returns the configured GCP project ID, ignoring placeholder values."""
        project = os.getenv("GCP_PROJECT_ID", "").strip()
        if not project or project in PLACEHOLDER_PROJECTS:
            return None
        return project

    def _get_client(self):
        """
        Lazily initialize Google Cloud Storage client.

        Supports:
        1. GOOGLE_APPLICATION_CREDENTIALS: If set and file exists, explicitly loads credentials
           (extracts service account private key, email, and project ID).
        2. Native Application Default Credentials (ADC): Cloud Run, Compute Engine, GKE, etc.
        """
        if self._client is not None:
            return self._client

        gac_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "").strip().strip('"').strip("'")
        if gac_path:
            if not os.path.isabs(gac_path):
                candidates = [
                    os.path.abspath(gac_path),
                    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), gac_path),
                ]
                for cand in candidates:
                    if os.path.isfile(cand):
                        gac_path = cand
                        break
                else:
                    gac_path = os.path.abspath(gac_path)

            if not os.path.isfile(gac_path):
                logger.warning(f"GOOGLE_APPLICATION_CREDENTIALS file does not exist: {gac_path}")

        project = self._get_configured_project()

        try:
            from google.cloud import storage

            # 1. If GOOGLE_APPLICATION_CREDENTIALS points to an existing file, load explicitly
            if gac_path and os.path.isfile(gac_path):
                import google.auth
                credentials, file_project_id = google.auth.load_credentials_from_file(gac_path)
                effective_project = project or file_project_id or getattr(credentials, "project_id", None)
                self._client = storage.Client(credentials=credentials, project=effective_project)
                logger.info(f"GCS client initialized using GOOGLE_APPLICATION_CREDENTIALS: {gac_path}")
                return self._client

            # 2. Native Application Default Credentials (ADC) for Cloud Run / GCE
            kwargs = {}
            if project:
                kwargs["project"] = project

            self._client = storage.Client(**kwargs)
            logger.info("GCS client initialized using native Application Default Credentials (ADC)")
            return self._client
        except Exception as e:
            logger.warning(f"GCS Client initialization failed: {e}")
            return None

    def _get_signing_credentials(self) -> Tuple[Optional[str], Optional[str]]:
        """
        Retrieves (service_account_email, access_token) for IAM SignBlob URL signing
        when running in environments without a local private key (e.g. Cloud Run / GCE / local ADC).
        """
        client = self._get_client()
        credentials = getattr(client, "_credentials", None) if client else None

        sa_email = (
            os.getenv("GCS_SERVICE_ACCOUNT_EMAIL", "").strip()
            or os.getenv("SERVICE_ACCOUNT_EMAIL", "").strip()
            or None
        )
        access_token = None

        if credentials is not None:
            if not sa_email:
                sa_email = getattr(credentials, "service_account_email", "") or getattr(
                    credentials, "signer_email", ""
                )
            try:
                from google.auth.transport.requests import Request

                # Check if token is present and valid; refresh if needed
                is_valid = getattr(credentials, "valid", False)
                token = getattr(credentials, "token", None)
                if not is_valid or not token:
                    req = Request()
                    credentials.refresh(req)

                access_token = getattr(credentials, "token", None)
            except Exception as e:
                logger.debug(f"Could not refresh credentials for signing: {e}")

        # In GCP environments (Cloud Run / GCE), if service_account_email is 'default' or missing,
        # query the metadata server directly.
        if not sa_email or sa_email == "default" or not access_token:
            try:
                from google.auth.compute_engine import _metadata
                from google.auth.transport.requests import Request

                req = Request()
                if not sa_email or sa_email == "default":
                    info = _metadata.get_service_account_info(req, service_account="default")
                    if info and "email" in info:
                        sa_email = info["email"]
                if not access_token:
                    tok, _ = _metadata.get_service_account_token(req, service_account="default")
                    access_token = tok
            except Exception as e:
                logger.debug(f"Could not retrieve service account info from metadata server: {e}")

        clean_email = sa_email if sa_email and sa_email != "default" else None
        return (clean_email, access_token)

    def _sign_blob(self, blob, expiration: timedelta = timedelta(hours=24)) -> str:
        """
        Generates a v4 signed URL for a GCS blob.
        Supports:
        1. Local credentials with private key (e.g. Service Account JSON from GOOGLE_APPLICATION_CREDENTIALS).
        2. GCP Managed Environments without local private keys (Cloud Run / GCE) via IAM SignBlob.
        3. Direct v4 fallback (handles mocked blob / clients in tests).
        """
        if blob is None:
            return ""

        client = self._get_client()
        credentials = getattr(client, "_credentials", None) if client else None

        # 1. If credentials can sign locally with a private key (Service Account JSON)
        can_sign_locally = (
            credentials is not None
            and (
                (hasattr(credentials, "signer") and credentials.signer is not None)
                or (hasattr(credentials, "sign_bytes") and callable(getattr(credentials, "sign_bytes", None)))
            )
        )

        if can_sign_locally:
            try:
                return blob.generate_signed_url(
                    version="v4",
                    expiration=expiration,
                    method="GET",
                )
            except Exception as e:
                logger.warning(f"Local v4 signing failed for blob {getattr(blob, 'name', '')}: {e}")

        # 2. Managed GCP / ADC environment without local private key: IAM SignBlob via service_account_email + access_token
        sa_email, access_token = self._get_signing_credentials()
        if sa_email and access_token:
            try:
                return blob.generate_signed_url(
                    version="v4",
                    expiration=expiration,
                    method="GET",
                    service_account_email=sa_email,
                    access_token=access_token,
                )
            except Exception as e:
                logger.warning(
                    f"Failed to generate signed URL via IAM SignBlob for {getattr(blob, 'name', '')}: {e}. "
                    f"Ensure {sa_email} has the 'roles/iam.serviceAccountTokenCreator' role on itself and the IAM Credentials API is enabled."
                )

        # 3. Direct v4 fallback (handles mocked blob / clients in tests)
        if not can_sign_locally:
            try:
                return blob.generate_signed_url(
                    version="v4",
                    expiration=expiration,
                    method="GET",
                )
            except Exception as e:
                logger.warning(
                    f"Signed URL generation failed for blob {getattr(blob, 'name', '')}: {e}. "
                    "Note: Generating a signed URL requires a Service Account JSON key (GOOGLE_APPLICATION_CREDENTIALS), "
                    "or IAM SignBlob permissions ('roles/iam.serviceAccountTokenCreator') on Cloud Run."
                )

        return ""

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
        bucket_name = self._get_configured_bucket()
        client = self._get_client()

        # In production, require GCS client and bucket to be properly configured
        if os.getenv("APP_ENV") == "production" and (not client or not bucket_name):
            logger.error("GCS configuration missing in production: bucket_name or client is not initialized.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Cloud Storage is not configured properly.",
            )

        effective_bucket = bucket_name or "storage"

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
            if client and bucket_name:
                try:
                    bucket = client.bucket(bucket_name)
                    target_blob = bucket.blob(blob_name)
                    target_blob.upload_from_string(
                        file_bytes,
                        content_type=content_type,
                        timeout=self.timeout_seconds,
                    )
                    signed_url = self._sign_blob(target_blob, expiration=timedelta(hours=24))
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"GCS upload failed for file {file.filename}: {error_msg}")
                    if os.getenv("APP_ENV") == "production":
                        raise HTTPException(
                            status_code=status.HTTP_502_BAD_GATEWAY,
                            detail=f"Cloud Storage upload failed for file {file.filename}: {error_msg}",
                        )
            else:
                if not bucket_name:
                    logger.warning(
                        f"GCS_BUCKET_NAME is not configured or is a placeholder ('{os.getenv('GCS_BUCKET_NAME', '')}') in .env. "
                        "Cloud upload and signed URL generation were skipped."
                    )
                elif not client:
                    logger.warning(
                        "GCS client is not authenticated (GOOGLE_APPLICATION_CREDENTIALS or ADC missing). "
                        "Cloud upload and signed URL generation were skipped."
                    )

            public_url = self._generate_public_url(blob_name, effective_bucket)
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

            bucket_name = self._get_configured_bucket()
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

            if not blob_name or not bucket_name:
                return ""

            client = self._get_client()
            if client and bucket_name:
                try:
                    bucket = client.bucket(bucket_name)
                    blob = bucket.blob(blob_name)
                    return self._sign_blob(
                        blob, expiration=timedelta(hours=expiration_hours)
                    )
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
