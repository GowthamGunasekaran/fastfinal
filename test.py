import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from fastapi import FastAPI, File, UploadFile, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import storage

# --- Configuration ---
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "your-gcp-project-id")
BUCKET_NAME = os.getenv("GCP_BUCKET_NAME", "your-bucket-name")
SERVICE_ACCOUNT_KEY_PATH = os.getenv("GCP_KEY_PATH", "path/to/service-account.json")

storage_client = None
bucket = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global storage_client, bucket
    # Initialize GCS client once on startup to reuse connection pools
    storage_client = storage.Client.from_service_account_json(
        SERVICE_ACCOUNT_KEY_PATH, project=PROJECT_ID
    )
    bucket = storage_client.bucket(BUCKET_NAME)
    yield


app = FastAPI(lifespan=lifespan)

# Allow React app access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _upload_single_to_gcp(file: UploadFile) -> dict:
    """Streams a single file directly into Google Cloud Storage."""
    try:
        ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
        unique_blob_name = f"uploads/{uuid.uuid4().hex}.{ext}"

        blob = bucket.blob(unique_blob_name)

        # Upload directly from the memory/spool buffer
        blob.upload_from_file(
            file.file,
            content_type=file.content_type,
            rewind=True,
        )

        # Direct GCS Public URL
        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{unique_blob_name}"

        return {
            "original_name": file.filename,
            "filename": unique_blob_name,
            "url": public_url,
        }
    finally:
        file.file.close()


@app.post("/upload-images", status_code=status.HTTP_201_CREATED)
def upload_images(files: list[UploadFile] = File(...)):
    # 1. Enforce 1-3 images constraint
    if len(files) < 1 or len(files) > 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must upload between 1 and 3 images.",
        )

    # 2. Validate MIME types
    for file in files:
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File '{file.filename}' is not a valid image.",
            )

    # 3. Parallel upload using threads (reduces 3-image upload time to ~1 image duration)
    try:
        with ThreadPoolExecutor(max_workers=3) as executor:
            uploaded_results = list(executor.map(_upload_single_to_gcp, files))

        return {
            "status": "success",
            "count": len(uploaded_results),
            "data": uploaded_results,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"GCS Upload failed: {str(e)}",
        )
