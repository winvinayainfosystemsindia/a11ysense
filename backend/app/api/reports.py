import os
import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response, JSONResponse, FileResponse, HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from common.database.connection import get_db
from common.database.models import AuditSession, ViolationRecord
from common.config import get_audit_storage_path
from backend.app.core.reporting.excel_generator import generate_excel_report

from backend.app.core.audit.orchestrator import audit_orchestrator
from common.constants.rule_catalog import resolve_rule

logger = logging.getLogger("a11ysense.api.reports")
router = APIRouter(tags=["Reports"])

@router.get("/api/reports/excel/{task_id}")
@router.get("/report/{task_id}/export")
async def download_excel_report(task_id: str, db: Session = Depends(get_db)):
    """
    Generates and downloads the executive Excel report with full test case & defect data.
    Loads testcase_report_{task_id}.json if available, falling back to DB for legacy audits.
    """
    testcases = await audit_orchestrator.get_testcase_report(task_id)
    session = db.query(AuditSession).filter(AuditSession.task_id == task_id).first()

    if not testcases and not session:
        raise HTTPException(status_code=404, detail="Audit session not found")

    if testcases:
        violations = [tc for tc in testcases if tc.get("status") == "FAIL"]
        passes = [tc for tc in testcases if tc.get("status") == "PASS"]
        not_applicable = [tc for tc in testcases if tc.get("status") == "NOT_APPLICABLE"]
        manual_review = [tc for tc in testcases if tc.get("status") == "MANUAL_REVIEW"]

        pages_scanned = sorted(list({
            tc.get("page_url") for tc in testcases
            if tc.get("page_url") and tc.get("page_url") not in ("All pages", "N/A")
        }))
        if not pages_scanned and session:
            pages_scanned = [session.url]

        audit_data = {
            "task_id": task_id,
            "url": session.url if session else (pages_scanned[0] if pages_scanned else ""),
            "summary": session.summary if session else {},
            "testcases": testcases,
            "violations": violations,
            "passes": passes,
            "not_applicable": not_applicable,
            "manual_review": manual_review,
            "pages_scanned": pages_scanned
        }
    else:
        # Fall back to DB only if JSON report is missing (e.g. legacy audit)
        violations_db = db.query(ViolationRecord).filter(ViolationRecord.audit_session_id == session.id).all()
        violations = []
        for v in violations_db:
            meta = v.metadata_json or {}
            rule = resolve_rule(v.rule_id)
            violations.append({
                "rule_id": v.rule_id,
                "impact": v.impact,
                "description": v.description,
                "help": v.help,
                "help_url": v.help_url,
                "nodes": v.nodes,
                "metadata_json": meta,
                "page_url": session.url,
                "wcag_criteria": f"{rule.wcag_sc} {rule.wcag_sc_name}",
                "wcag_level": rule.level,
                "wcag_principle": rule.principle,
                "expected_result": meta.get("expected_result", "Element must meet WCAG criteria."),
                "actual_result": meta.get("actual_result", v.help),
                "steps_to_reproduce": meta.get("steps_to_reproduce", "1. Navigate to page.\n2. Inspect element."),
                "remediation_plan": meta.get("remediation_plan", "Fix accessibility defect."),
                "remarks": "Legacy audit: re-run for the full report"
            })

        audit_data = {
            "task_id": task_id,
            "url": session.url,
            "summary": session.summary or {},
            "testcases": [],
            "violations": violations,
            "passes": [],
            "pages_scanned": [session.url]
        }

    excel_bytes = generate_excel_report(audit_data)
    filename = f"A11ySense_Audit_Report_{task_id}.xlsx"

    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/api/reports/json/{task_id}")
async def get_report_json(task_id: str, db: Session = Depends(get_db)):
    """Return raw audit results JSON."""
    session = db.query(AuditSession).filter(AuditSession.task_id == task_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Audit session not found")
    
    violations_db = db.query(ViolationRecord).filter(ViolationRecord.audit_session_id == session.id).all()
    
    return {
        "task_id": task_id,
        "url": session.url,
        "timestamp": session.timestamp.isoformat() if session.timestamp else "",
        "summary": session.summary,
        "violations_count": len(violations_db),
        "violations": [
            {
                "rule_id": v.rule_id,
                "impact": v.impact,
                "description": v.description,
                "help": v.help,
                "help_url": v.help_url,
                "nodes": v.nodes,
                "metadata": v.metadata_json
            }
            for v in violations_db
        ]
    }

@router.get("/api/reports/{task_id}/screenshot/{filename}")
@router.get("/report/{task_id}/screenshot/{filename}")
async def get_screenshot(task_id: str, filename: str):
    """Serve captured defect screenshot locally from audit storage directory."""
    # Prevent directory traversal attacks
    clean_filename = os.path.basename(filename)
    reports_dir = get_audit_storage_path(task_id, create=False)
    filepath = os.path.join(reports_dir, clean_filename)
    
    if not os.path.exists(filepath):
        # Fallback search in general storage
        storage_base = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../storage"))
        for root, _, files in os.walk(storage_base):
            if clean_filename in files:
                filepath = os.path.join(root, clean_filename)
                break

    if os.path.exists(filepath):
        return FileResponse(filepath, media_type="image/png")
    
    raise HTTPException(status_code=404, detail="Screenshot not found")

@router.get("/report/{task_id}")
@router.get("/api/reports/{task_id}")
async def view_report(task_id: str, db: Session = Depends(get_db)):
    """Executive view for compliance report in the monolith."""
    session = db.query(AuditSession).filter(AuditSession.task_id == task_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Audit session not found")

    summary = session.summary or {}
    score = summary.get("accessibility_score", 100)
    violations = summary.get("total_violations", 0)
    passes = summary.get("passes_count", 0)
    status = session.status or "completed"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>A11ySense Audit Report — {task_id}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 40px 20px; }}
        .container {{ max-width: 900px; margin: 0 auto; background: #1e293b; border-radius: 16px; border: 1px solid #334155; padding: 32px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }}
        h1 {{ margin-top: 0; font-size: 28px; color: #ffffff; display: flex; align-items: center; justify-content: space-between; }}
        .badge {{ font-size: 14px; padding: 4px 12px; border-radius: 9999px; background: #059669; color: #ecfdf5; text-transform: uppercase; }}
        .url {{ color: #94a3b8; font-size: 16px; word-break: break-all; margin-bottom: 24px; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin: 24px 0; }}
        .card {{ background: #0f172a; border: 1px solid #334155; border-radius: 12px; padding: 20px; text-align: center; }}
        .card-num {{ font-size: 36px; font-weight: 800; margin: 4px 0; }}
        .card-label {{ font-size: 13px; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.5px; }}
        .score {{ color: #10b981; }}
        .violations {{ color: #ef4444; }}
        .passes {{ color: #3b82f6; }}
        .actions {{ margin-top: 32px; display: flex; gap: 16px; justify-content: flex-end; }}
        .btn {{ display: inline-flex; align-items: center; padding: 12px 24px; border-radius: 8px; font-weight: 600; text-decoration: none; cursor: pointer; transition: 0.2s; }}
        .btn-primary {{ background: #2563eb; color: #ffffff; border: none; }}
        .btn-primary:hover {{ background: #1d4ed8; }}
        .btn-secondary {{ background: #334155; color: #f8fafc; border: 1px solid #475569; }}
        .btn-secondary:hover {{ background: #475569; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>
            A11ySense Accessibility Report
            <span class="badge">{status}</span>
        </h1>
        <div class="url">Target: <strong>{session.url}</strong></div>
        <div class="grid">
            <div class="card">
                <div class="card-label">Accessibility Score</div>
                <div class="card-num score">{score}%</div>
            </div>
            <div class="card">
                <div class="card-label">Total Violations</div>
                <div class="card-num violations">{violations}</div>
            </div>
            <div class="card">
                <div class="card-label">Passed Checks</div>
                <div class="card-num passes">{passes}</div>
            </div>
        </div>
        <div class="actions">
            <a href="/report/{task_id}/export" class="btn btn-primary">Download Executive Excel Report</a>
            <a href="http://localhost:5173/org/{session.organization_id}/audits/{task_id}" class="btn btn-secondary">Open in Dashboard</a>
        </div>
    </div>
</body>
</html>
"""
    return HTMLResponse(content=html)
