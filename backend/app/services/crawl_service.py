"""
Crawl Service handling URL discovery, sitemap crawling, and crawl task state.
"""
import uuid
import logging
from typing import Optional
from sqlalchemy.orm import Session
from common.database.models import CrawlProgress, User
from common.schemas.audit import CrawlDiscoveryRequest
from backend.app.task_queue import task_queue
from backend.app.core.audit.orchestrator import AuditOrchestrator

logger = logging.getLogger(__name__)

class CrawlService:
    def __init__(self):
        self.orchestrator = AuditOrchestrator()

    def start_crawl_discovery(self, db: Session, req: CrawlDiscoveryRequest, current_user: User) -> str:
        crawl_task_id = f"crawl-{uuid.uuid4().hex[:12]}"
        crawl_record = CrawlProgress(
            crawl_task_id=crawl_task_id,
            url=req.url,
            scan_target=req.scan_target,
            status="crawling",
            organization_id=current_user.organization_id
        )
        db.add(crawl_record)
        db.commit()

        task_queue.run_task(
            self.orchestrator.run_crawl_discovery_flow,
            crawl_task_id,
            req,
            str(current_user.organization_id)
        )
        return crawl_task_id

    def get_crawl_progress(self, db: Session, crawl_task_id: str) -> Optional[CrawlProgress]:
        return db.query(CrawlProgress).filter(CrawlProgress.crawl_task_id == crawl_task_id).first()

crawl_service = CrawlService()
