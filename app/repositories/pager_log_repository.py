"""
Repository for PagerLog database operations.

Follows repository pattern — no business logic, only DB queries.
"""

from typing import List
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.pager_log import PagerLog


class PagerLogRepository:

    def create_log(self, db: Session, log: PagerLog) -> PagerLog:
        """Insert a new pager_log row and flush (no commit — caller commits)."""
        db.add(log)
        db.flush()
        return log

    def get_logs_by_email(
        self, db: Session, email: str, limit: int = 10
    ) -> List[PagerLog]:
        """
        Fetch pager_log rows where created_by OR last_updated_by matches *email*.
        Ordered by created_at DESC. Limited to *limit* rows (default 10).
        """
        stmt = (
            select(PagerLog)
            .where(
                or_(
                    PagerLog.created_by == email,
                    PagerLog.last_updated_by == email,
                )
            )
            .order_by(PagerLog.created_at.desc())
            .limit(limit)
        )
        return list(db.scalars(stmt).all())


pager_log_repository = PagerLogRepository()
