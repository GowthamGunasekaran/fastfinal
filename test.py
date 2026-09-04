import os
import uuid
import traceback
from datetime import timedelta
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from google.cloud import storage

app = FastAPI()

# Replace with your actual GCP Project ID and Bucket ID (or pass via Environment Variables)
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "")
GCP_BUCKET_ID = os.getenv("GCS_BUCKET_NAME", os.getenv("GCP_BUCKET_ID", ""))


def _generate_signed_url(blob, client, expiration_hours: int = 24) -> str:
    """
    Generates a v4 signed URL for a blob using Service Account IAM SignBlob.
    """
    if blob is None:
        return ""

    expiration = timedelta(hours=expiration_hours)
    try:
        from google.auth.transport.requests import Request
        import google.auth

        auth_creds = getattr(client, "_credentials", None)
        if auth_creds is None:
            auth_creds, _ = google.auth.default()

        if not getattr(auth_creds, "valid", False) or not getattr(auth_creds, "token", None):
            auth_creds.refresh(Request())

        access_token = getattr(auth_creds, "token", None)

        sa_email = (
            os.getenv("GCS_SERVICE_ACCOUNT_EMAIL", "").strip()
            or os.getenv("SERVICE_ACCOUNT_EMAIL", "").strip()
            or getattr(auth_creds, "service_account_email", "")
            or getattr(auth_creds, "signer_email", "")
        )

        if not sa_email or sa_email == "default":
            try:
                from google.auth.compute_engine import _metadata
                req = Request()
                info = _metadata.get_service_account_info(req, service_account="default")
                if info and "email" in info:
                    sa_email = info["email"]
            except Exception as meta_err:
                print(f"Could not query metadata server: {meta_err}")

        if sa_email and sa_email != "default" and access_token:
            return blob.generate_signed_url(
                version="v4",
                expiration=expiration,
                method="GET",
                service_account_email=sa_email,
                access_token=access_token,
            )
    except Exception as iam_err:
        print(f"IAM SignBlob URL generation failed: {iam_err}")

    # Fallback
    try:
        return blob.generate_signed_url(
            version="v4",
            expiration=expiration,
            method="GET",
        )
    except Exception:
        return ""


@app.post("/upload")
def upload_image_to_gcp(file: UploadFile = File(...)):
    try:
        # Establish connection directly using GCP environment credentials
        storage_client = storage.Client(project=GCP_PROJECT_ID)
        bucket = storage_client.bucket(GCP_BUCKET_ID)

        # Generate a unique filename to avoid overwrites
        file_ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
        blob_name = f"{uuid.uuid4().hex}.{file_ext}"
        blob = bucket.blob(blob_name)

        # Upload the file stream directly into the GCP bucket
        blob.upload_from_file(
            file.file,
            content_type=file.content_type,
            rewind=True
        )

        # Construct the GCP URL
        gcp_url = f"https://storage.googleapis.com/{GCP_BUCKET_ID}/{blob_name}"

        # Generate signed URL (valid for 24 hours)
        signed_url = _generate_signed_url(blob, storage_client)

        return {
            "status": "success",
            "filename": blob_name,
            "url": gcp_url,
            "signed_url": signed_url,
        }

    except Exception as e:
        # Catch and return the exact error message and stack trace for debugging
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "traceback": traceback.format_exc()
            }
        )
    finally:
        file.file.close()
