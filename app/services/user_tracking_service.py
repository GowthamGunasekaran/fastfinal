"""
Service layer for user tracking:
- Record login events (login_log)
- Record action events (action_log: VIEW, EXPORT, DRAFT, TRACK, etc.)
- Upload and upsert user profiles from CSV (user_details)
"""

import csv
import io
from typing import List, Optional
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.models.action_log import ActionLog
from app.models.login_log import LoginLog
from app.models.user_details import UserDetails
from app.repositories.user_tracking_repository import user_tracking_repository
from app.schemas.user_tracking_schema import (
    ActionLogCreate,
    LoginLogCreate,
    UserDetailsOut,
    UserDetailsUploadResponse,
)
from app.utils.helpers import generate_uuid, utcnow


class UserTrackingService:

    def record_login(self, db: Session, payload: LoginLogCreate) -> LoginLog:
        """Create a new login_log entry."""
        log = LoginLog(
            id=generate_uuid(),
            user_email=payload.user_email.strip() if payload.user_email else None,
            role=payload.role.strip() if payload.role else None,
            login_time=utcnow(),
        )
        return user_tracking_repository.create_login_log(db, log)

    def record_action(self, db: Session, payload: ActionLogCreate) -> ActionLog:
        """
        Create a new action_log entry.
        Action can be VIEW, EXPORT, DRAFT, TRACK, or any custom action string.
        """
        log = ActionLog(
            id=generate_uuid(),
            pager_id=payload.pager_id.strip() if payload.pager_id else None,
            user_email=payload.user_email.strip() if payload.user_email else None,
            role=payload.role.strip() if payload.role else None,
            market=payload.market.strip() if payload.market else None,
            action=payload.action.strip() if payload.action else None,
            date_time=utcnow(),
        )
        return user_tracking_repository.create_action_log(db, log)

    def get_user_details(self, db: Session, email: str) -> UserDetails:
        """
        Fetch a user_details record by email.
        Raises 404 if the user is not found.
        """
        cleaned_email = email.strip()
        user = user_tracking_repository.get_user_by_email(db, cleaned_email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User details not found for email: {cleaned_email}",
            )
        return user

    async def upload_user_details_csv(
        self, db: Session, file: UploadFile
    ) -> UserDetailsUploadResponse:
        """
        Parse an uploaded CSV file containing columns:
        - email_id (or email)
        - role
        - market

        Performs an UPSERT into user_details:
        - Inserts if email does not exist.
        - Updates role, market, and last_updated_at if email exists.
        """
        if not file.filename.lower().endswith((".csv", ".txt")):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only CSV files (.csv) are accepted.",
            )

        content_bytes = await file.read()
        if not content_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The uploaded CSV file is empty.",
            )

        # Decode with utf-8-sig (handles Excel BOM) or utf-8
        try:
            content_text = content_bytes.decode("utf-8-sig")
        except UnicodeDecodeError:
            try:
                content_text = content_bytes.decode("utf-8")
            except UnicodeDecodeError:
                content_text = content_bytes.decode("latin-1")

        csv_reader = csv.DictReader(io.StringIO(content_text))
        if not csv_reader.fieldnames:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not parse headers from CSV file.",
            )

        # Normalize field names to detect email_id / email, role, market
        header_map = {}
        for raw_header in csv_reader.fieldnames:
            if not raw_header:
                continue
            cleaned = raw_header.strip().lower().replace(" ", "_")
            if cleaned in ("email_id", "email", "emailid", "user_email", "useremail"):
                header_map["email"] = raw_header
            elif cleaned in ("role", "user_role", "userrole"):
                header_map["role"] = raw_header
            elif cleaned in ("market", "user_market", "region"):
                header_map["market"] = raw_header

        if "email" not in header_map:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CSV must contain an 'email_id' or 'email' column.",
            )

        inserted_count = 0
        updated_count = 0
        processed_users: List[UserDetails] = []

        for row_idx, row in enumerate(csv_reader, start=1):
            raw_email = row.get(header_map["email"])
            if not raw_email or not raw_email.strip():
                continue  # Skip blank rows

            email = raw_email.strip()
            role = row.get(header_map["role"]).strip() if header_map.get("role") and row.get(header_map["role"]) else None
            market = row.get(header_map["market"]).strip() if header_map.get("market") and row.get(header_map["market"]) else None

            user, was_inserted = user_tracking_repository.upsert_user_details(
                db, email=email, role=role, market=market
            )
            if was_inserted:
                inserted_count += 1
            else:
                updated_count += 1

            processed_users.append(user)

        db.commit()

        # Refresh all processed users to return updated values
        for user in processed_users:
            db.refresh(user)

        return UserDetailsUploadResponse(
            message="User details processed successfully.",
            total_processed=len(processed_users),
            inserted=inserted_count,
            updated=updated_count,
            users=[UserDetailsOut.model_validate(u) for u in processed_users],
        )


user_tracking_service = UserTrackingService()
