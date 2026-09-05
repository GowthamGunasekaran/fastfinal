"""
FastAPI application entry point.
"""

import os
from contextlib import asynccontextmanager

from typing import Optional, List
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()

from app.db import engine, Base

# Import all models so SQLAlchemy registers them before create_all
from app.models import Pager, Pillar, PillarInitiative, Metadata, Campaign  # noqa: F401

# API router
from app.api.v1.router import router
from app.schemas.storage_schema import ImageUploadItem
from app.services.storage_service import storage_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan: create tables and seed data on startup (skip in test mode).
    """
    if os.getenv("TESTING") != "1":
        # Create all tables
        Base.metadata.create_all(bind=engine)

        # Seed development data
        from app.db import SessionLocal
        from app.seed import run_seed
        db = SessionLocal()
        try:
            run_seed(db)
        finally:
            db.close()

    yield  # Application runs here


# ---------------------------------------------------------------------------
# FastAPI Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title=os.getenv("APP_TITLE", "National One-Pager API"),
    description=(
        "Backend API for creating, managing, and publishing National One-Pagers. "
        "Supports a hierarchical Pager → Pillar → Initiative structure with "
        "WEIGHTED/UNWEIGHTED scoring modes."
    ),
    version=os.getenv("APP_VERSION", "1.0.0"),
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Include router
# ---------------------------------------------------------------------------

app.include_router(router)


@app.get("/health", tags=["Health"])
def health_check():
    """Service health check endpoint."""
    return {"status": "ok", "service": "National One-Pager API"}


@app.post(
    "/upload-image",
    response_model=List[ImageUploadItem],
    status_code=201,
    tags=["Upload"],
    summary="Root upload image endpoint",
)
async def upload_image_root(
    files: Optional[List[UploadFile]] = File(None),
    file: Optional[UploadFile] = File(None),
):
    upload_list = []
    if files:
        upload_list.extend(files)
    if file:
        upload_list.append(file)
    if not upload_list:
        raise HTTPException(status_code=400, detail="No file selected")
    return await storage_service.upload_images(files=upload_list)

