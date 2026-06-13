"""
AuditProgressRepo — PostgreSQL-backed repository for live audit progress.

Replaces the in-memory ACTIVE_TASKS dict as the single source of truth.
All writes are committed immediately so any reader (across restarts or
multiple instances) sees consistent state.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Optional, List

from common.database.connection import get_session_local
from common.database.models import AuditProgress
from app.schemas import AuditTask

logger = logging.getLogger(__name__)


class AuditProgressRepo:
    """Thread-safe repository for AuditProgress rows.

    Every public method opens its own short-lived DB session and commits
    immediately, matching the pattern already used by agent/app/main.py
    for AuditSession operations.
    """

    # ── Write operations ────────────────────────────────────────────────────

    def create(self, task_id: str, url: str, depth: int = 1) -> AuditTask:
        """Insert a new progress row when an audit starts."""
        db = get_session_local()()
        try:
            row = AuditProgress(
                task_id=task_id,
                url=url,
                status="processing",
                pages_found=0,
                pages_completed=0,
                pages_total=0,
                pages_scanned=[],
                pages_discovered=[],
                depth=depth,
            )
            db.add(row)
            db.commit()
            db.refresh(row)
            return self.to_audit_task(row)
        except Exception as e:
            db.rollback()
            logger.error(f"[AuditProgressRepo] create failed for {task_id}: {e}")
            raise
        finally:
            db.close()

    def set_status(self, task_id: str, status: str) -> None:
        """Update only the status field (e.g. crawling → auditing)."""
        self._patch(task_id, {"status": status})

    def set_pages(
        self,
        task_id: str,
        *,
        pages_found: int,
        pages_total: int,
        pages_discovered: List[str],
    ) -> None:
        """Record how many pages were discovered after the crawl phase."""
        self._patch(task_id, {
            "pages_found": pages_found,
            "pages_total": pages_total,
            "pages_discovered": pages_discovered,
        })

    def increment_completed(self, task_id: str, scanned_url: str) -> None:
        """Atomically increment pages_completed and append the scanned URL."""
        db = get_session_local()()
        try:
            row = db.query(AuditProgress).filter_by(task_id=task_id).first()
            if row:
                row.pages_completed = (row.pages_completed or 0) + 1
                scanned = list(row.pages_scanned or [])
                scanned.append(scanned_url)
                row.pages_scanned = scanned
                row.updated_at = datetime.utcnow()
                db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"[AuditProgressRepo] increment_completed failed for {task_id}: {e}")
        finally:
            db.close()

    def mark_completed(self, task_id: str, token_usage: dict, report_url: Optional[str] = None) -> None:
        """Mark audit as completed and store token usage + report URL."""
        self._patch(task_id, {
            "status": "completed",
            "token_usage": token_usage,
            "report_url": report_url,
        })

    def mark_failed(self, task_id: str, error: str, token_usage: Optional[dict] = None) -> None:
        """Mark audit as failed and store the error message."""
        payload = {"status": "failed", "error": error}
        if token_usage is not None:
            payload["token_usage"] = token_usage
        self._patch(task_id, payload)

    # ── Read operations ─────────────────────────────────────────────────────

    def get(self, task_id: str) -> Optional[AuditTask]:
        """Fetch the current progress row for a task_id and return as AuditTask."""
        db = get_session_local()()
        try:
            row = db.query(AuditProgress).filter_by(task_id=task_id).first()
            if row:
                return self.to_audit_task(row)
            return None
        except Exception as e:
            logger.error(f"[AuditProgressRepo] get failed for {task_id}: {e}")
            return None
        finally:
            db.close()

    def to_audit_task(self, row: AuditProgress) -> AuditTask:
        """Convert an AuditProgress DB row to the AuditTask API schema."""
        return AuditTask(
            task_id=row.task_id,
            status=row.status,
            url=row.url,
            created_at=row.created_at,
            pages_found=row.pages_found or 0,
            pages_completed=row.pages_completed or 0,
            pages_total=row.pages_total or 0,
            pages_scanned=row.pages_scanned or [],
            pages_discovered=row.pages_discovered or [],
            report_url=row.report_url,
            error=row.error,
            token_usage=row.token_usage,
            depth=row.depth or 1,
        )

    def as_audit_task(self, task_id: str) -> Optional[AuditTask]:
        """Convenience: fetch + convert in one call."""
        return self.get(task_id)

    def delete(self, task_id: str) -> None:
        """Delete progress row from the database."""
        db = get_session_local()()
        try:
            db.query(AuditProgress).filter_by(task_id=task_id).delete()
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"[AuditProgressRepo] delete failed for {task_id}: {e}")
        finally:
            db.close()

    # ── Internal ────────────────────────────────────────────────────────────

    def _patch(self, task_id: str, fields: dict) -> None:
        """Generic partial-update helper."""
        db = get_session_local()()
        try:
            row = db.query(AuditProgress).filter_by(task_id=task_id).first()
            if row:
                for key, value in fields.items():
                    setattr(row, key, value)
                row.updated_at = datetime.utcnow()
                db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"[AuditProgressRepo] _patch({task_id}, {list(fields.keys())}) failed: {e}")
        finally:
            db.close()


# Global singleton — import this everywhere instead of ACTIVE_TASKS
audit_progress_repo = AuditProgressRepo()
