"""
Repository for user tracking operations:
- LoginLog
- ActionLog
- UserDetails (upsert)
"""

from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.action_log import ActionLog
from app.models.login_log import LoginLog
from app.models.user_details import UserDetails
from app.utils.helpers import utcnow


class UserTrackingRepository:

    def create_login_log(self, db: Session, log: LoginLog) -> LoginLog:
        """Insert a LoginLog record and commit."""
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    def create_action_log(self, db: Session, log: ActionLog) -> ActionLog:
        """Insert an ActionLog record and commit."""
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    def get_user_by_email(self, db: Session, email: str) -> Optional[UserDetails]:
        """Find a UserDetails record by primary key email."""
        return db.query(UserDetails).filter(UserDetails.email == email).first()

    def upsert_user_details(
        self, db: Session, email: str, role: Optional[str], market: Optional[str]
    ) -> Tuple[UserDetails, bool]:
        """
        Upsert a UserDetails row.
        If email exists -> update role, market, last_updated_at.
        If email does not exist -> insert new record.
        Returns (UserDetails, was_inserted).
        Caller handles commit or batch commit.
        """
        user = self.get_user_by_email(db, email)
        now = utcnow()
        if user:
            if role is not None:
                user.role = role
            if market is not None:
                user.market = market
            user.last_updated_at = now
            db.flush()
            return user, False
        else:
            new_user = UserDetails(
                email=email,
                role=role,
                market=market,
                created_at=now,
                last_updated_at=now,
            )
            db.add(new_user)
            db.flush()
            return new_user, True

    def list_users(self, db: Session) -> List[UserDetails]:
        """Return all user_details rows."""
        return db.query(UserDetails).order_by(UserDetails.email).all()


user_tracking_repository = UserTrackingRepository()
