"""
CrawlProgressRepo — PostgreSQL-backed repository for async crawl-only
discovery tasks (the "Discover pages" wizard step), polled by the frontend
before the user selects which pages to audit. Mirrors AuditProgressRepo.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional, Dict, Any

from common.database.connection import get_session_local
from common.database.models import CrawlProgress
from common.schemas.audit import CrawlDiscoveryTask

logger = logging.getLogger(__name__)


class CrawlProgressRepo:
    """Each public method opens its own short-lived DB session and commits immediately."""

    def create(self, crawl_task_id: str, url: str, scan_target: str, organization_id: Optional[str], project_id: Optional[str]) -> CrawlDiscoveryTask:
        db = get_session_local()()
        try:
            row = CrawlProgress(
                crawl_task_id=crawl_task_id,
                url=url,
                scan_target=scan_target,
                status="queued",
                pages_discovered=[],
                sitemaps_found=[],
                unauth_pages_discovered=[],
                auth_pages_discovered=[],
                organization_id=organization_id,
                project_id=project_id,
            )
            db.add(row)
            db.commit()
            db.refresh(row)
            return self.to_crawl_task(row)
        except Exception as e:
            db.rollback()
            logger.error(f"[CrawlProgressRepo] create failed for {crawl_task_id}: {e}")
            raise
        finally:
            db.close()

    def set_status(self, crawl_task_id: str, status: str) -> None:
        self._patch(crawl_task_id, {"status": status})

    def set_result(self, crawl_task_id: str, *, pages_discovered, pages_depth_map, url_to_menu_text,
                    sitemaps_found, unauth_pages_discovered, auth_pages_discovered,
                    storage_state, auth_headers) -> None:
        self._patch(crawl_task_id, {
            "status": "completed",
            "pages_discovered": pages_discovered,
            "pages_depth_map": pages_depth_map,
            "url_to_menu_text": url_to_menu_text,
            "sitemaps_found": sitemaps_found,
            "unauth_pages_discovered": unauth_pages_discovered,
            "auth_pages_discovered": auth_pages_discovered,
            "storage_state": storage_state,
            "auth_headers": auth_headers,
        })

    def mark_failed(self, crawl_task_id: str, error: str) -> None:
        self._patch(crawl_task_id, {"status": "failed", "error": error})

    def get(self, crawl_task_id: str) -> Optional[CrawlDiscoveryTask]:
        db = get_session_local()()
        try:
            row = db.query(CrawlProgress).filter_by(crawl_task_id=crawl_task_id).first()
            if row:
                return self.to_crawl_task(row)
            return None
        except Exception as e:
            logger.error(f"[CrawlProgressRepo] get failed for {crawl_task_id}: {e}")
            return None
        finally:
            db.close()

    def get_auth_context(self, crawl_task_id: str) -> Optional[Dict[str, Any]]:
        """Fetch just the carried-forward auth session for a completed discovery run."""
        db = get_session_local()()
        try:
            row = db.query(CrawlProgress).filter_by(crawl_task_id=crawl_task_id).first()
            if not row:
                return None
            return {
                "storage_state": row.storage_state,
                "auth_headers": row.auth_headers or {},
                "pages_depth_map": row.pages_depth_map or {},
                "url_to_menu_text": row.url_to_menu_text or {},
                "sitemaps_found": row.sitemaps_found or [],
            }
        except Exception as e:
            logger.error(f"[CrawlProgressRepo] get_auth_context failed for {crawl_task_id}: {e}")
            return None
        finally:
            db.close()

    def to_crawl_task(self, row: CrawlProgress) -> CrawlDiscoveryTask:
        return CrawlDiscoveryTask(
            crawl_task_id=row.crawl_task_id,
            status=row.status,
            url=row.url,
            pages_discovered=row.pages_discovered or [],
            pages_depth_map=row.pages_depth_map or {},
            url_to_menu_text=row.url_to_menu_text or {},
            sitemaps_found=row.sitemaps_found or [],
            unauth_pages_discovered=row.unauth_pages_discovered or [],
            auth_pages_discovered=row.auth_pages_discovered or [],
            error=row.error,
            created_at=row.created_at,
        )

    def _patch(self, crawl_task_id: str, fields: dict) -> None:
        db = get_session_local()()
        try:
            row = db.query(CrawlProgress).filter_by(crawl_task_id=crawl_task_id).first()
            if row:
                for key, value in fields.items():
                    setattr(row, key, value)
                row.updated_at = datetime.utcnow()
                db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"[CrawlProgressRepo] _patch({crawl_task_id}, {list(fields.keys())}) failed: {e}")
        finally:
            db.close()


crawl_progress_repo = CrawlProgressRepo()
