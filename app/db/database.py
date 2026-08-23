"""
Database connection and session management.

Supports dual configuration options:
1. Local SQLite (development default)
2. GCP Hosted PostgreSQL / Cloud SQL (production / cloud deployment)

Configured dynamically via .env environment variables:
- DB_TYPE (sqlite | postgresql)
- DATABASE_URL
- DB_USER, DB_PASSWORD, DB_NAME, DB_SCHEMA, DB_HOST, DB_PORT
- INSTANCE_CONNECTION_NAME (GCP Cloud SQL instance connection string)
"""

import os
import logging
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Dynamic Database URL Construction
# ---------------------------------------------------------------------------

def build_database_url() -> str:
    """
    Constructs the database connection URL based on environment variables.
    Supports local SQLite or GCP hosted PostgreSQL.
    """
    db_type = os.getenv("DB_TYPE", "").lower().strip()
    env_db_url = os.getenv("DATABASE_URL", "").strip()
    
    db_user = os.getenv("DB_USER", "").strip()
    db_pass = os.getenv("DB_PASSWORD", "").strip()
    db_host = os.getenv("DB_HOST", "").strip()
    db_port = os.getenv("DB_PORT", "5432").strip()
    db_name = os.getenv("DB_NAME", "").strip()
    instance_connection = os.getenv("INSTANCE_CONNECTION_NAME", "").strip()

    # If DB_TYPE is explicitly postgresql or postgresql parameters exist
    if db_type == "postgresql" or (db_user and db_name and not env_db_url.startswith("sqlite")):
        if instance_connection and not db_host:
            # Cloud SQL Unix Socket Connection (e.g. /cloudsql/project:region:instance)
            socket_path = f"/cloudsql/{instance_connection}"
            return f"postgresql+psycopg2://{db_user}:{db_pass}@/{db_name}?host={socket_path}"
        
        host = db_host or "localhost"
        return f"postgresql+psycopg2://{db_user}:{db_pass}@{host}:{db_port}/{db_name}"

    if env_db_url:
        if env_db_url.startswith("postgresql://"):
            return env_db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
        return env_db_url

    # Default to local SQLite database
    return "sqlite:///./national_one_pager.db"


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

# Enable WAL mode for SQLite (improves concurrent read/write performance)
if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

# Configure schema search_path for PostgreSQL if specified
if DATABASE_URL.startswith("postgresql"):
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
    FastAPI dependency that provides a transactional database session per request.
    Automatically closes session upon request completion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
