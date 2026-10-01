"""
Report Service for generating Excel reports and JSON summaries.
"""
import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from common.database.models import AuditSession, ViolationRecord
from backend.app.core.reporting.excel_generator import generate_excel_report

logger = logging.getLogger(__name__)

class ReportService:
    def generate_excel_for_task(self, db: Session, task_id: str) -> Optional[bytes]:
        session = db.query(AuditSession).filter(AuditSession.task_id == task_id).first()
        if not session:
            return None

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
                "metadata_json": v.metadata_json or {},
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
        return generate_excel_report(audit_data)

    def get_json_report(self, db: Session, task_id: str) -> Optional[Dict[str, Any]]:
        session = db.query(AuditSession).filter(AuditSession.task_id == task_id).first()
        if not session:
            return None

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

report_service = ReportService()
