"""
Pytest configuration — shared fixtures for all tests.
Uses an in-memory SQLite database to avoid affecting the real database.
"""

import os

TEST_DATABASE_URL = "sqlite:///:memory:"
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["TESTING"] = "1"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base, get_db
from app.main import app

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=test_engine
)


@pytest.fixture(scope="session", autouse=True)
def create_test_tables():
    """Create all tables once for the entire test session."""
    # Import models so they register with Base
    from app.models import Pager, Pillar, PillarInitiative, Metadata, Campaign  # noqa
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db():
    """Provide a fresh transaction-rolled-back session per test."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db):
    """Provide a TestClient that uses the test database session."""

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def mock_storage_for_tests(monkeypatch):
    """
    Mock GCS storage bucket for test suite to run in isolation without network calls.
    Allows testing upload validation, formatting, and signed URLs cleanly.
    """
    from unittest.mock import MagicMock
    from app.services.storage_service import storage_service

    mock_bucket = MagicMock()
    mock_blob = MagicMock()
    mock_bucket.blob.return_value = mock_blob
    mock_blob.generate_signed_url.return_value = "https://storage.googleapis.com/test-bucket/images/test.png?signed=true"

    orig_bucket = storage_service.bucket
    orig_bucket_name = storage_service.bucket_name
    storage_service.bucket = mock_bucket
    storage_service.bucket_name = "test-bucket"

    yield

    storage_service.bucket = orig_bucket
    storage_service.bucket_name = orig_bucket_name

