"""
CrawlerTaskRepository — Handles Event Bus streams consumption and publication for background crawl worker.
"""
import logging
from common.utils.event_bus import read_events, publish_event

logger = logging.getLogger(__name__)


class CrawlerTaskRepository:

    def get_next_tasks(self, last_id: str, block_ms: int = 2000) -> list:
        """Read new events from the 'audit:tasks' Redis stream."""
        try:
            return read_events("audit:tasks", last_id=last_id, block_ms=block_ms) or []
        except Exception as e:
            logger.error(f"[CrawlerTaskRepository] Error reading events: {e}")
            return []

    def publish_crawl_result(self, result_payload: dict) -> None:
        """Publish completed crawl outcomes onto stream 'crawl:results'."""
        try:
            publish_event("crawl:results", result_payload)
        except Exception as e:
            logger.error(f"[CrawlerTaskRepository] Error publishing crawl result: {e}")
            raise


crawler_task_repo = CrawlerTaskRepository()
