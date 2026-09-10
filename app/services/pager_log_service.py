"""
Service for writing and reading PagerLog records.

Action derivation from pager status:
  DRAFT     → DRAFTED
  PUBLISHED → EDITED
  DELETED   → DELETED
  ARCHIVED  → ARCHIVED
  (initial creation always uses CREATE)
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.pager import Pager
from app.models.pager_log import PagerLog
from app.repositories.pager_log_repository import pager_log_repository
from app.utils.enums import PagerAction, PagerStatus
from app.utils.helpers import utcnow


def _action_from_status(status: PagerStatus) -> PagerAction:
    """Map a PagerStatus to the corresponding PagerAction log label."""
    mapping = {
        PagerStatus.DRAFT: PagerAction.DRAFTED,
        PagerStatus.PUBLISHED: PagerAction.EDITED,
        PagerStatus.DELETED: PagerAction.DELETED,
        PagerStatus.ARCHIVED: PagerAction.ARCHIVED,
    }
    return mapping.get(status, PagerAction.EDITED)


class PagerLogService:

    def write_create_log(
        self, db: Session, pager: Pager, actor_email: Optional[str]
    ) -> PagerLog:
        """
        Insert a CREATE log entry.
        Sets created_by and created_at; last_updated_by / last_modified_at are null.
        """
        log = PagerLog(
            pager_id=pager.pager_id,
            action=PagerAction.CREATE,
            created_by=actor_email,
            last_updated_by=None,
            created_at=utcnow(),
            last_modified_at=None,
            payload=self._build_payload(pager),
        )
        return pager_log_repository.create_log(db, log)

    def write_update_log(
        self, db: Session, pager: Pager, actor_email: Optional[str]
    ) -> PagerLog:
        """
        Insert an update log entry.
        Action is derived from the pager's current status.
        Sets last_updated_by and last_modified_at; created_by / created_at are null.
        """
        action = _action_from_status(pager.status)
        log = PagerLog(
            pager_id=pager.pager_id,
            action=action,
            created_by=None,
            last_updated_by=actor_email,
            created_at=None,
            last_modified_at=utcnow(),
            payload=self._build_payload(pager),
        )
        return pager_log_repository.create_log(db, log)

    def write_status_log(
        self,
        db: Session,
        pager: Pager,
        new_status: PagerStatus,
        actor_email: Optional[str],
    ) -> PagerLog:
        """
        Insert a status-change log entry.
        Action is derived from *new_status* (already applied to pager.status by caller).
        """
        action = _action_from_status(new_status)
        log = PagerLog(
            pager_id=pager.pager_id,
            action=action,
            created_by=None,
            last_updated_by=actor_email,
            created_at=None,
            last_modified_at=utcnow(),
            payload=self._build_payload(pager),
        )
        return pager_log_repository.create_log(db, log)

    def get_logs_by_email(
        self, db: Session, email: str, limit: int = 10
    ) -> List[PagerLog]:
        """Return the most recent *limit* logs where the actor matches *email*."""
        return pager_log_repository.get_logs_by_email(db, email, limit=limit)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_payload(self, pager: Pager) -> dict:
        """Serialize the pager's current scalar fields into a JSON-safe dict."""
        return {
            "pager_id": pager.pager_id,
            "title": pager.title,
            "market": pager.market,
            "retailer": pager.retailer,
            "channel": pager.channel,
            "category": pager.category,
            "campaign_focus": pager.campaign_focus,
            "business_group": pager.business_group,
            "year": pager.year,
            "business_outcome_statement": pager.business_outcome_statement,
            "scoring_mode": pager.scoring_mode,
            "status": pager.status,
            "track": pager.track,
            "pager_type": pager.pager_type,
            "image_url": pager.image_url,
            "created_by": pager.created_by,
            "updated_by": pager.updated_by,
            "published_by": pager.published_by,
            "created_at": pager.created_at.isoformat() if pager.created_at else None,
            "updated_at": pager.updated_at.isoformat() if pager.updated_at else None,
            "published_at": pager.published_at.isoformat() if pager.published_at else None,
        }


pager_log_service = PagerLogService()
