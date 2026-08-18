"""
FastAPI application entry point.
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()

from app.db.database import engine, Base

# Import all models so SQLAlchemy registers them before create_all
from app.db.models import Pager, Pillar, PillarInitiative, Metadata, Campaign  # noqa: F401

from app.api.v1.router import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan: create tables and seed data on startup.
    """
    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Seed development data
    from app.db.database import SessionLocal
    from app.db.seed import run_seed
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
    return {"status": "ok", "service": "National One-Pager API"}
