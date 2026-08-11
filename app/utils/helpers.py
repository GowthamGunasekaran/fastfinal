import uuid
from datetime import datetime, timezone


def generate_uuid() -> str:
    """Generate a new UUID string."""
    return str(uuid.uuid4())


def utcnow() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)
