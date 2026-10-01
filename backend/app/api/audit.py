import uuid
import logging
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from common.database.connection import get_db
from common.database.models import User, AuditProgress, CrawlProgress, AuditSession, Project
from common.auth.deps import get_current_user
from common.schemas.audit import AuditRequest, CrawlDiscoveryRequest
from backend.app.task_queue import task_queue
from backend.app.core.audit.orchestrator import AuditOrchestrator

logger = logging.getLogger("a11ysense.api.audit")
router = APIRouter(tags=["Audit Engine"])
orchestrator = AuditOrchestrator()

@router.get("/api/audits")
async def list_audits(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all audit sessions for the authenticated user's organization."""
    sessions = db.query(AuditSession).filter(
        AuditSession.organization_id == current_user.organization_id
    ).order_by(AuditSession.created_at.desc()).all()

    result = []
    for s in sessions:
        summary = s.summary or {}
        project_name = s.project.name if s.project else "Default Project"
        dt = s.timestamp or s.created_at
        result.append({
            "task_id": s.task_id,
            "url": s.url,
            "timestamp": dt.isoformat() if dt else "",
            "status": s.status,
            "accessibility_score": summary.get("accessibility_score", 100.0),
            "total_violations": summary.get("total_violations", 0),
            "project_name": project_name
        })
    return result

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

    return {
        "crawl_task_id": crawl_task_id,
        "status": "crawling",
        "url": req.url,
        "pages_discovered": [],
        "pages_depth_map": {},
        "sitemaps_found": [],
        "unauth_pages_discovered": [],
        "auth_pages_discovered": [],
        "error": None
    }

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

    eff_proj_id = project_id
    if not eff_proj_id:
        p = db.query(Project).filter(Project.organization_id == current_user.organization_id).first()
        eff_proj_id = p.id if p else None

    # Bootstraps AuditSession so the running audit immediately displays in the Audits History table
    session_rec = AuditSession(
        task_id=task_id,
        url=req.url,
        status="auditing",
        depth=req.depth,
        project_id=eff_proj_id,
        organization_id=current_user.organization_id,
        summary={"accessibility_score": 100, "total_violations": 0}
    )
    db.add(session_rec)

    progress = AuditProgress(
        task_id=task_id,
        url=req.url,
        status="auditing",
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
    session = db.query(AuditSession).filter(AuditSession.task_id == task_id).first()

    if not rec and not session:
        raise HTTPException(status_code=404, detail="Audit task not found")

    status_val = rec.status if rec else (session.status if session else "completed")
    url_val = rec.url if rec else (session.url if session else "")
    pages_scanned = (rec.pages_scanned if rec else None) or ([url_val] if url_val else [])
    pages_discovered = (rec.pages_discovered if rec else None) or pages_scanned
    error_val = rec.error if rec else None
    report_url = (rec.report_url if rec else None) or f"/api/reports/excel/{task_id}"

    return {
        "task_id": task_id,
        "status": status_val,
        "url": url_val,
        "depth": rec.depth if rec else (session.depth if session else 1),
        "pages_found": rec.pages_found if rec else 1,
        "pages_completed": rec.pages_completed if rec else 1,
        "pages_total": rec.pages_total if rec else 1,
        "pages_scanned": pages_scanned,
        "pages_discovered": pages_discovered,
        "report_url": report_url,
        "error": error_val,
        "summary": session.summary if session else None
    }

@router.get("/task/{task_id}/token_usage")
async def get_task_token_usage(
    task_id: str,
    db: Session = Depends(get_db)
):
    """Get token usage stats for a task."""
    return await orchestrator.fetch_and_format_token_usage(task_id)

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

@router.post("/task/{task_id}/stop")
async def stop_audit(task_id: str):
    return await orchestrator.stop_audit(task_id)

@router.post("/task/{task_id}/pause")
async def pause_audit(task_id: str):
    return await orchestrator.pause_audit(task_id)

@router.post("/task/{task_id}/resume")
async def resume_audit(task_id: str):
    return await orchestrator.resume_audit(task_id)

@router.delete("/task/{task_id}")
async def delete_audit(task_id: str):
    return await orchestrator.delete_audit(task_id)
