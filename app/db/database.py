"""
Database connection and session management for PostgreSQL.

Supports two configuration modes:
1. GCP Hosted PostgreSQL (Cloud SQL) via Unix Socket (automatically enabled when `K_SERVICE` environment variable is present in Cloud Run)
2. Local PostgreSQL (default for local development when `K_SERVICE` is absent)
"""

import os
import logging
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Database Connection URL Builder (PostgreSQL Only)
# ---------------------------------------------------------------------------

def build_database_url() -> str:
    """
    Constructs PostgreSQL database connection URL.
    - Uses `DATABASE_URL` if explicitly set in environment.
    - If `K_SERVICE` is present (GCP Cloud Run), connects to Cloud SQL via unix socket.
    - Otherwise, connects to local PostgreSQL instance.
    """
    env_db_url = os.getenv("DATABASE_URL", "").strip()
    if env_db_url:
        if env_db_url.startswith("postgresql://"):
            return env_db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
        return env_db_url

    k_service = os.getenv("K_SERVICE", "").strip()
    db_user = os.getenv("DB_USER", "postgres").strip()
    db_pass = os.getenv("DB_PASSWORD", "postgres").strip()
    db_name = os.getenv("DB_NAME", "national_one_pager").strip()
    db_schema = os.getenv("DB_SCHEMA", "public").strip()

    if k_service:
        # GCP Cloud Run environment — connect via Cloud SQL Unix Socket
        instance_conn = os.getenv("INSTANCE_CONNECTION_NAME", "").strip()
        socket_path = instance_conn if instance_conn.startswith("/cloudsql/") else f"/cloudsql/{instance_conn}"
        
        url = f"postgresql+psycopg2://{db_user}:{db_pass}@/{db_name}?host={socket_path}"
        if db_schema and db_schema != "public":
            url += f"&options=-csearch_path%3D{db_schema}"
        return url
    else:
        # Local PostgreSQL environment
        db_host = os.getenv("DB_HOST", "localhost").strip()
        db_port = os.getenv("DB_PORT", "5432").strip()
        
        return f"postgresql+psycopg2://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"


DATABASE_URL: str = build_database_url()

# ---------------------------------------------------------------------------
# SQLAlchemy Engine Configuration
# ---------------------------------------------------------------------------

connect_args: dict = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True if not DATABASE_URL.startswith("sqlite") else False,
    echo=False,
)

# Configure schema search_path for PostgreSQL if specified
db_schema = os.getenv("DB_SCHEMA", "").strip()
if db_schema and db_schema != "public":
    @event.listens_for(engine, "connect")
    def set_postgres_schema(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute(f"SET search_path TO {db_schema}, public")
        cursor.close()

# ---------------------------------------------------------------------------
# Session & Base Setup
# ---------------------------------------------------------------------------

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# FastAPI Dependency
# ---------------------------------------------------------------------------

def get_db() -> Generator:
    """
    FastAPI dependency providing a database session per request.
    Automatically closes session upon request completion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
