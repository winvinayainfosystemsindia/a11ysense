import uuid
import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from common.database.connection import get_db
from common.database.models import User, AuditProgress, CrawlProgress, AuditSession, Project, TestCase
from common.auth.deps import get_current_user
from common.schemas.audit import AuditRequest, CrawlDiscoveryRequest
from backend.app.task_queue import task_queue
from backend.app.core.audit.orchestrator import AuditOrchestrator
from app.repository.testcase_repo import testcase_repo
from app.repository.session_repo import audit_session_repo
from app.core.regression import (
    compute_fingerprint,
    normalize_url,
    fingerprint_batch,
    MatchItem,
    match_groups,
)
from common.constants.rule_catalog import wcag_fields_for_row

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
            "run_number": s.run_number or 1,
            "run_type": s.run_type or "baseline",
            "score": s.score if s.score is not None else summary.get("accessibility_score", 100.0),
            "accessibility_score": s.score if s.score is not None else summary.get("accessibility_score", 100.0),
            "total_violations": s.fail_count if s.fail_count is not None else summary.get("total_violations", 0),
            "defects_new": s.defects_new,
            "defects_fixed": s.defects_fixed,
            "defects_reopened": s.defects_reopened,
            "defects_open": s.defects_open,
            "project_name": project_name,
            "project_id": str(s.project_id) if s.project_id else None
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
        str(current_user.organization_id),
        str(project_id) if project_id else None
    )

    return {
        "status": "crawling",
        "crawl_task_id": crawl_task_id,
        "url": req.url,
        "scan_target": req.scan_target,
        "pages_discovered": [],
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
    """Starts WCAG 2.2 Level A+AA accessibility audit run with regression sequencing."""
    task_id = f"task-{uuid.uuid4().hex[:12]}"

    eff_proj_id = project_id
    if not eff_proj_id:
        p = db.query(Project).filter(Project.organization_id == current_user.organization_id).first()
        eff_proj_id = p.id if p else None

    # Bootstraps AuditSession with run sequencing and regression link
    session_rec = audit_session_repo.bootstrap_session(
        task_id=task_id,
        url=str(req.url),
        org_id=str(current_user.organization_id),
        proj_id=str(eff_proj_id) if eff_proj_id else None,
        depth=req.depth,
        urls_subset=req.selected_urls
    )

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
        str(current_user.organization_id),
        str(eff_proj_id) if eff_proj_id else None
    )

    return {
        "status": "started",
        "task_id": task_id,
        "run_number": session_rec.run_number,
        "run_type": session_rec.run_type,
        "previous_run_id": str(session_rec.previous_run_id) if session_rec.previous_run_id else None
    }


@router.get("/api/audit/status/{task_id}")
@router.get("/task/{task_id}")
async def get_audit_status(
    task_id: str,
    db: Session = Depends(get_db)
):
    """Poll audit run status, regression counters, and progress."""
    rec = db.query(AuditProgress).filter(AuditProgress.task_id == task_id).first()
    session = db.query(AuditSession).filter(AuditSession.task_id == task_id).first()

    if not rec and not session:
        raise HTTPException(status_code=404, detail="Audit task not found")

    status_val = rec.status if rec else (session.status if session else "completed")
    url_val = rec.url if rec else (session.url if session else "")
    error_val = rec.error if rec else None

    pages_scanned = rec.pages_scanned if rec and rec.pages_scanned else []
    pages_discovered = rec.pages_discovered if rec and rec.pages_discovered else []
    report_url = (rec.report_url if rec else None) or f"/api/reports/excel/{task_id}"

    prev_run = session.previous_run if (session and session.previous_run_id) else None
    score_delta = round((session.score or 0.0) - (prev_run.score or 0.0), 1) if prev_run else 0.0

    created_at_dt = None
    if session and session.created_at:
        created_at_dt = session.created_at
    elif rec and getattr(rec, "created_at", None):
        created_at_dt = rec.created_at
    else:
        created_at_dt = datetime.utcnow()
    created_at_val = created_at_dt.isoformat() if hasattr(created_at_dt, "isoformat") else str(created_at_dt)

    summary_val = None
    if session and session.summary:
        summary_val = session.summary
    elif session:
        summary_val = {
            "accessibility_score": session.score if session.score is not None else 100.0,
            "total_violations": session.fail_count if session.fail_count is not None else 0,
            "passes_count": session.pass_count if session.pass_count is not None else 0,
            "total_testcases": session.total_testcases if session.total_testcases is not None else 0
        }

    token_usage_val = None
    try:
        token_usage_val = await orchestrator.fetch_and_format_token_usage(task_id)
    except Exception as e:
        logger.warning(f"Could not fetch token usage for {task_id}: {e}")

    return {
        "task_id": task_id,
        "status": status_val,
        "url": url_val,
        "depth": rec.depth if rec else (session.depth if session else 1),
        "run_number": session.run_number if session else 1,
        "run_type": session.run_type if session else "baseline",
        "previous_run_id": str(session.previous_run_id) if session and session.previous_run_id else None,
        "previous_run_number": prev_run.run_number if prev_run else None,
        "score": session.score if session else 100.0,
        "score_delta": score_delta,
        "defects_new": session.defects_new if session else 0,
        "defects_fixed": session.defects_fixed if session else 0,
        "defects_reopened": session.defects_reopened if session else 0,
        "defects_open": session.defects_open if session else 0,
        "defects_not_retested": session.defects_not_retested if session else 0,
        "pages_found": rec.pages_found if rec else 1,
        "pages_completed": rec.pages_completed if rec else 1,
        "pages_total": rec.pages_total if rec else 1,
        "pages_scanned": pages_scanned,
        "pages_discovered": pages_discovered,
        "report_url": report_url,
        "error": error_val,
        "summary": summary_val,
        "token_usage": token_usage_val,
        "created_at": created_at_val
    }


@router.get("/api/audits/{task_id}/regression")
async def get_audit_regression(
    task_id: str,
    db: Session = Depends(get_db)
):
    """Returns regression summary vs previous run."""
    session = db.query(AuditSession).filter(AuditSession.task_id == task_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Audit session not found")

    prev = session.previous_run if session.previous_run_id else None
    score_delta = round(session.score - (prev.score if prev else 0.0), 1) if prev else 0.0
    scope_changed = bool(prev and prev.scope_fingerprint != session.scope_fingerprint)

    return {
        "task_id": session.task_id,
        "run_number": session.run_number or 1,
        "run_type": session.run_type,
        "previous_run_id": str(session.previous_run_id) if session.previous_run_id else None,
        "previous_run_number": prev.run_number if prev else None,
        "score": session.score,
        "previous_score": prev.score if prev else 0.0,
        "score_delta": score_delta,
        "defects_new": session.defects_new,
        "defects_fixed": session.defects_fixed,
        "defects_reopened": session.defects_reopened,
        "defects_open": session.defects_open,
        "defects_not_retested": session.defects_not_retested,
        "scope_changed": scope_changed,
        "dynamic_groups_matched": (session.summary or {}).get("dynamic_groups_matched", 0) if session.summary else 0
    }


@router.get("/api/audits/{task_id}/testcases")
@router.get("/task/{task_id}/testcases")
async def get_task_testcases(
    task_id: str,
    status: Optional[str] = None,
    rule_id: Optional[str] = None,
    limit: Optional[int] = None,
    offset: int = 0,
    paginated: bool = False,
    db: Session = Depends(get_db)
):
    """Get test cases from DB (flat list by default, or paginated if requested)."""
    session = db.query(AuditSession).filter(AuditSession.task_id == task_id).first()
    if session:
        effective_limit = limit if limit is not None else (100 if paginated else None)
        db_items, total = testcase_repo.get_testcases_by_session(
            db, session.id, status=status, rule_id=rule_id, limit=effective_limit, offset=offset
        )
        counts = testcase_repo.count_testcases_by_status(db, session.id)

        items = []
        for tc in db_items:
            def_code = tc.defect.defect_code if tc.defect else ("DEF-0001" if tc.status == "FAIL" else "N/A")
            wf = wcag_fields_for_row(tc)
            items.append({
                "testcase_id": tc.testcase_code,
                "display_name": tc.display_name or tc.testcase_code,
                "rule_id": tc.rule_id,
                "testcase_name": tc.testcase_name,
                "status": tc.status,
                "severity": tc.severity,
                "criteria": wf["criteria"],
                "level": wf["level"],
                "principle": wf["principle"],
                "description": tc.description or "",
                "expected_result": tc.expected_result or "",
                "actual_result": tc.actual_result or "",
                "steps_to_reproduce": tc.steps_to_reproduce or "",
                "business_impact": tc.business_impact or "",
                "remediation": tc.remediation or "",
                "html_snippet": tc.html_snippet or "N/A",
                "selector": tc.selector or "N/A",
                "screenshot": tc.screenshot_path or "N/A",
                "repeat_count": tc.repeat_count or 1,
                "remarks": tc.remarks or "",
                "help_url": tc.help_url or "",
                "page_url": tc.page_url or "",
                "page_title": tc.page_title or "",
                "defect_id": def_code
            })

        if not paginated:
            return items

        return {
            "items": items,
            "total": total,
            "limit": effective_limit,
            "offset": offset,
            "counts": counts
        }

    # Fallback to json report
    tc_json = await orchestrator.get_testcase_report(task_id)
    if tc_json:
        filtered = tc_json
        if status:
            filtered = [x for x in filtered if x.get("status") == status.upper()]
        if rule_id:
            filtered = [x for x in filtered if x.get("rule_id") == rule_id]
        total = len(filtered)
        if not paginated:
            return filtered

        effective_limit = limit if limit is not None else 100
        paginated_items = filtered[offset:offset + effective_limit]
        counts = {
            "PASS": sum(1 for x in tc_json if x.get("status") == "PASS"),
            "FAIL": sum(1 for x in tc_json if x.get("status") == "FAIL"),
            "NOT_APPLICABLE": sum(1 for x in tc_json if x.get("status") == "NOT_APPLICABLE"),
            "MANUAL_REVIEW": sum(1 for x in tc_json if x.get("status") == "MANUAL_REVIEW")
        }
        return {
            "items": paginated_items,
            "total": total,
            "limit": effective_limit,
            "offset": offset,
            "counts": counts
        }

    return [] if not paginated else {"items": [], "total": 0, "limit": limit or 100, "offset": offset, "counts": {}}


@router.get("/api/audits/{task_id_a}/compare/{task_id_b}")
async def compare_audits(
    task_id_a: str,
    task_id_b: str,
    db: Session = Depends(get_db)
):
    """
    Diff comparison between two audit runs.
    Returns:
    - Fixed: defects that failed in run A but passed / absent in run B
    - New: defects that failed in run B but were absent in run A
    - Unchanged: defects failing in both runs
    """
    session_a = db.query(AuditSession).filter(AuditSession.task_id == task_id_a).first()
    session_b = db.query(AuditSession).filter(AuditSession.task_id == task_id_b).first()

    if not session_a or not session_b:
        raise HTTPException(status_code=404, detail="One or both audit sessions not found")

    tcs_a = testcase_repo.get_all_testcases_by_session(db, session_a.id)
    tcs_b = testcase_repo.get_all_testcases_by_session(db, session_b.id)

    fails_a = [tc for tc in tcs_a if tc.status == "FAIL"]
    fails_b = [tc for tc in tcs_b if tc.status == "FAIL"]

    recs_a = [
        {"rule_id": tc.rule_id, "html": tc.html_snippet or "", "page_url": tc.page_url or "", "criteria": tc.wcag_criteria or ""}
        for tc in fails_a
    ]
    recs_b = [
        {"rule_id": tc.rule_id, "html": tc.html_snippet or "", "page_url": tc.page_url or "", "criteria": tc.wcag_criteria or ""}
        for tc in fails_b
    ]

    fps_a = fingerprint_batch(recs_a) if recs_a else []
    fps_b = fingerprint_batch(recs_b) if recs_b else []

    items_a = [
        MatchItem(ref=tc, fp=r.fp, dynamic=r.dynamic, order=r.occurrence)
        for tc, r in zip(fails_a, fps_a)
    ]
    items_b = [
        MatchItem(ref=tc, fp=r.fp, dynamic=r.dynamic, order=r.occurrence)
        for tc, r in zip(fails_b, fps_b)
    ]

    m_res = match_groups(items_a, items_b)

    fixed = []
    for p_item in m_res.unmatched_prev:
        tc = p_item.ref
        fixed.append({
            "testcase_code": tc.testcase_code,
            "defect_code": tc.defect.defect_code if tc.defect else "DEF-0001",
            "title": tc.testcase_name,
            "rule_id": tc.rule_id,
            "page_url": tc.page_url,
            "severity": tc.severity,
            "status": "Fixed in Run #" + str(session_b.run_number or 2)
        })

    new_defects = []
    for c_item in m_res.new:
        tc = c_item.ref
        new_defects.append({
            "testcase_code": tc.testcase_code,
            "defect_code": tc.defect.defect_code if tc.defect else "DEF-0001",
            "title": tc.testcase_name,
            "rule_id": tc.rule_id,
            "page_url": tc.page_url,
            "severity": tc.severity,
            "status": "New in Run #" + str(session_b.run_number or 2)
        })

    unchanged = []
    for _p_item, c_item in m_res.pairs:
        tc = c_item.ref
        unchanged.append({
            "testcase_code": tc.testcase_code,
            "defect_code": tc.defect.defect_code if tc.defect else "DEF-0001",
            "title": tc.testcase_name,
            "rule_id": tc.rule_id,
            "page_url": tc.page_url,
            "severity": tc.severity,
            "status": "Still Failing"
        })

    return {
        "run_a": {
            "task_id": session_a.task_id,
            "run_number": session_a.run_number or 1,
            "score": session_a.score,
            "total_violations": session_a.fail_count
        },
        "run_b": {
            "task_id": session_b.task_id,
            "run_number": session_b.run_number or 2,
            "score": session_b.score,
            "total_violations": session_b.fail_count
        },
        "fixed": fixed,
        "new": new_defects,
        "unchanged": unchanged,
        "fixed_count": len(fixed),
        "new_count": len(new_defects),
        "unchanged_count": len(unchanged),
        "dynamic_groups_matched": m_res.dynamic_groups_matched,
        "score_delta": round(session_b.score - session_a.score, 1)
    }


@router.get("/task/{task_id}/token_usage")
async def get_task_token_usage(
    task_id: str,
    db: Session = Depends(get_db)
):
    """Get token usage stats for a task."""
    return await orchestrator.fetch_and_format_token_usage(task_id)


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
