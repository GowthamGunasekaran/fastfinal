"""
Pydantic schemas for user tracking:
- LoginLogCreate / LoginLogOut
- ActionLogCreate / ActionLogOut
- UserDetailsOut / UserDetailsUploadResponse
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class LoginLogCreate(BaseModel):
    user_email: str
    role: Optional[str] = None


class LoginLogOut(BaseModel):
    id: str
    user_email: Optional[str] = None
    role: Optional[str] = None
    login_time: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ActionLogCreate(BaseModel):
    pager_id: Optional[str] = None
    user_email: Optional[str] = None
    role: Optional[str] = None
    market: Optional[str] = None
    action: str  # e.g., VIEW, EXPORT, DRAFT, TRACK, or any custom action string


class ActionLogOut(BaseModel):
    id: str
    pager_id: Optional[str] = None
    user_email: Optional[str] = None
    role: Optional[str] = None
    market: Optional[str] = None
    date_time: Optional[datetime] = None
    action: Optional[str] = None

    model_config = {"from_attributes": True}


class UserDetailsOut(BaseModel):
    email: str
    role: Optional[str] = None
    market: Optional[str] = None
    created_at: Optional[datetime] = None
    last_updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UserDetailsUploadResponse(BaseModel):
    message: str
    total_processed: int
    inserted: int
    updated: int
    users: List[UserDetailsOut] = []
