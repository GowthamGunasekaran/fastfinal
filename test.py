import os
import uuid
import traceback
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from google.cloud import storage

app = FastAPI()

# Replace with your actual GCP Project ID and Bucket ID (or pass via Environment Variables)
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "")
GCP_BUCKET_ID = os.getenv("GCS_BUCKET_NAME", os.getenv("GCP_BUCKET_ID", ""))


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

        return {
            "status": "success",
            "filename": blob_name,
            "url": gcp_url
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
