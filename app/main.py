from fastapi import FastAPI

from app.api.v1.router import router as v1_router
from app.db.database import create_tables

create_tables()

app = FastAPI(
    title="National One-Pager API",
    version="1.0.0",
    description="National One-Pager API using FastAPI, SQLAlchemy and SQLite.",
)

app.include_router(v1_router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
