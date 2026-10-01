import os
import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response, JSONResponse, FileResponse
from sqlalchemy.orm import Session

from common.database.connection import get_db
from common.database.models import AuditSession, ViolationRecord
from backend.app.core.reporting.excel_generator import generate_excel_report

logger = logging.getLogger("a11ysense.api.reports")
router = APIRouter(prefix="/api/reports", tags=["Reports"])

@router.get("/excel/{task_id}")
async def download_excel_report(task_id: str, db: Session = Depends(get_db)):
    """
    Generates and downloads the executive 3-sheet Excel report:
    Sheet 1: Defect Report (Red #8B0000)
    Sheet 2: Test Case Report (Blue #1a237e)
    Sheet 3: WCAG Criteria Reference (Light Blue #1565c0)
    """
    session = db.query(AuditSession).filter(AuditSession.task_id == task_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Audit session not found")

    violations_db = db.query(ViolationRecord).filter(ViolationRecord.audit_session_id == session.id).all()
    
    violations = []
    for v in violations_db:
        violations.append({
            "rule_id": v.rule_id,
            "impact": v.impact,
            "description": v.description,
            "help": v.help,
            "help_url": v.help_url,
            "nodes": v.nodes,
            "page_url": session.url,
            "wcag_criteria": (v.metadata_json or {}).get("wcag_criteria", "1.1.1 Non-text Content"),
            "wcag_level": (v.metadata_json or {}).get("wcag_level", "A"),
            "expected_result": (v.metadata_json or {}).get("expected_result", "Element must meet WCAG criteria."),
            "actual_result": (v.metadata_json or {}).get("actual_result", v.help),
            "steps_to_reproduce": (v.metadata_json or {}).get("steps_to_reproduce", "1. Navigate to page.\n2. Inspect element."),
            "remediation_plan": (v.metadata_json or {}).get("remediation_plan", "Fix accessibility defect.")
        })

    audit_data = {
        "task_id": task_id,
        "url": session.url,
        "summary": session.summary or {},
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

@router.get("/json/{task_id}")
async def get_report_json(task_id: str, db: Session = Depends(get_db)):
    """Return raw audit results JSON."""
    session = db.query(AuditSession).filter(AuditSession.task_id == task_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Audit session not found")
    
    violations_db = db.query(ViolationRecord).filter(ViolationRecord.audit_session_id == session.id).all()
    
    return {
        "task_id": task_id,
        "url": session.url,
        "timestamp": session.timestamp.isoformat(),
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
