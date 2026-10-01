import uuid
import logging
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from common.database.connection import get_db
from common.database.models import User, AuditProgress, CrawlProgress, AuditSession
from common.auth.deps import get_current_user
from common.schemas.audit import AuditRequest, CrawlDiscoveryRequest
from backend.app.task_queue import task_queue
from backend.app.core.audit.orchestrator import AuditOrchestrator

logger = logging.getLogger("a11ysense.api.audit")
router = APIRouter(tags=["Audit Engine"])
orchestrator = AuditOrchestrator()

@router.post("/api/audit/discover")
@router.post("/crawl_discovery")
async def start_crawl_discovery(
    req: CrawlDiscoveryRequest,
    project_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Starts async page discovery crawl for web page or web application."""
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
        orchestrator.run_crawl_discovery_flow,
        crawl_task_id,
        req,
        str(current_user.organization_id)
    )

    return {"status": "started", "crawl_task_id": crawl_task_id}

@router.get("/api/audit/discover/{crawl_task_id}")
@router.get("/crawl_discovery/{crawl_task_id}")
async def get_crawl_discovery_status(
    crawl_task_id: str,
    db: Session = Depends(get_db)
):
    """Poll discovery crawl progress."""
    rec = db.query(CrawlProgress).filter(CrawlProgress.crawl_task_id == crawl_task_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Discovery task not found")
    return {
        "crawl_task_id": rec.crawl_task_id,
        "status": rec.status,
        "url": rec.url,
        "pages_discovered": rec.pages_discovered or [],
        "pages_depth_map": rec.pages_depth_map or {},
        "sitemaps_found": rec.sitemaps_found or [],
        "unauth_pages_discovered": rec.unauth_pages_discovered or [],
        "auth_pages_discovered": rec.auth_pages_discovered or [],
        "error": rec.error
    }

@router.post("/api/audit/start")
@router.post("/start_audit")
async def start_audit(
    req: AuditRequest,
    project_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Starts WCAG 2.2 Level A+AA accessibility audit run."""
    task_id = f"task-{uuid.uuid4().hex[:12]}"
    progress = AuditProgress(
        task_id=task_id,
        url=req.url,
        status="processing",
        depth=req.depth
    )
    db.add(progress)
    db.commit()

    task_queue.run_task(
        orchestrator.run_in_memory_audit_flow,
        task_id,
        req,
        str(current_user.organization_id)
    )

    return {"status": "started", "task_id": task_id}

@router.get("/api/audit/status/{task_id}")
@router.get("/task/{task_id}")
async def get_audit_status(
    task_id: str,
    db: Session = Depends(get_db)
):
    """Poll audit run status and progress counters."""
    rec = db.query(AuditProgress).filter(AuditProgress.task_id == task_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Audit task not found")
    return {
        "task_id": rec.task_id,
        "status": rec.status,
        "url": rec.url,
        "pages_found": rec.pages_found,
        "pages_completed": rec.pages_completed,
        "pages_total": rec.pages_total,
        "pages_scanned": rec.pages_scanned or [],
        "report_url": rec.report_url,
        "error": rec.error
    }

@router.get("/task/{task_id}/token_usage")
async def get_task_token_usage(
    task_id: str,
    db: Session = Depends(get_db)
):
    """Get token usage stats for a task."""
    return await orchestrator.get_llm_token_usage(task_id)

@router.get("/task/{task_id}/testcases")
async def get_task_testcases(
    task_id: str,
    db: Session = Depends(get_db)
):
    """Get generated test cases for a task."""
    session = db.query(AuditSession).filter(AuditSession.task_id == task_id).first()
    if not session:
        return []
    return (session.summary or {}).get("test_cases", [])
