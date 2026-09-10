"""
Pydantic schemas for PagerLog responses.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel


class PagerLogOut(BaseModel):
    """Response schema for a single pager_log record."""

    pager_log_id: int
    pager_id: str

    # Actor fields
    created_by: Optional[str] = None
    last_updated_by: Optional[str] = None

    # Timestamps
    created_at: Optional[datetime] = None
    last_modified_at: Optional[datetime] = None

    # Action label: CREATE | EDITED | DELETED | ARCHIVED | DRAFTED
    action: str

    # Full JSON payload that triggered this action
    payload: Optional[Dict[str, Any]] = None

    model_config = {"from_attributes": True}
