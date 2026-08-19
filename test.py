import os
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, File, HTTPException, UploadFile, status
from google.cloud import storage

# --- Configuration ---
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "your-gcp-project-id")
BUCKET_NAME = os.getenv("GCP_BUCKET_NAME", "your-bucket-id")
SERVICE_ACCOUNT_KEY_PATH = os.getenv(
    "GCP_KEY_PATH", "path/to/service-account.json"
)

storage_client = None
bucket = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global storage_client, bucket
    # Initialize client once on startup to avoid connection overhead per request
    storage_client = storage.Client.from_service_account_json(
        SERVICE_ACCOUNT_KEY_PATH, project=PROJECT_ID
    )
    bucket = storage_client.bucket(BUCKET_NAME)
    yield


app = FastAPI(lifespan=lifespan)


# Define with regular `def` (not `async def`) so FastAPI automatically runs
# the blocking Google Cloud Storage SDK calls in a separate thread pool.
@app.post("/upload", status_code=status.HTTP_201_CREATED)
def upload_image(file: UploadFile = File(...)):
    # Validate MIME type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must be an image.",
        )

    # Generate a unique file name to avoid collisions
    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    unique_filename = f"{uuid.uuid4().hex}.{ext}"

    try:
        blob = bucket.blob(unique_filename)

        # Upload directly from SpooledTemporaryFile stream (zero intermediate disk copy)
        blob.upload_from_file(
            file.file,
            content_type=file.content_type,
            rewind=True,
        )

        # Direct GCS URL (accessible if the bucket/object has public read permissions)
        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{unique_filename}"

        return {
            "filename": unique_filename,
            "url": public_url,
            "content_type": file.content_type,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}",
        )
    finally:
        file.file.close()
