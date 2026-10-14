"""
Report Service for building audit data from database and generating Excel/JSON reports.
"""
import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from common.database.models import AuditSession, ViolationRecord, TestCase, Defect
from app.repository.testcase_repo import testcase_repo
from backend.app.core.reporting.excel_generator import generate_excel_report
from backend.app.core.audit.orchestrator import audit_orchestrator

logger = logging.getLogger(__name__)


class ReportService:
    def build_audit_data(
        self,
        db: Optional[Session],
        task_id: str,
        testcases_fallback: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Loads full audit data from PostgreSQL for reports, feeds generate_excel_report.
        Falls back to JSON or legacy violation records if database testcases are absent.
        """
        session = db.query(AuditSession).filter(AuditSession.task_id == task_id).first() if db else None

        # 1. Load testcases from DB if session exists
        db_testcases = []
        if session:
            try:
                db_testcases = testcase_repo.get_all_testcases_by_session(db, session.id)
            except Exception as e:
                logger.warning(f"Error fetching DB testcases for session {session.id}: {e}")
                db_testcases = []

        if db_testcases:
            all_tcs = []
            violations = []
            passes = []
            not_applicable = []
            manual_review = []

            for tc in db_testcases:
                defect_code = "N/A"
                defect_status = None
                defect_first_seen = None
                defect_last_seen = None
                defect_fixed_in = None
                defect_reopen_count = 0
                defect_times_seen = 1
                defect_age_days = 0

                if tc.defect:
                    d = tc.defect
                    defect_code = d.defect_code
                    defect_status = d.status
                    defect_first_seen = d.first_seen_run.run_number if d.first_seen_run else 1
                    defect_last_seen = d.last_seen_run.run_number if d.last_seen_run else session.run_number
                    defect_fixed_in = d.fixed_in_run.run_number if d.fixed_in_run else None
                    defect_reopen_count = d.reopen_count
                    defect_times_seen = d.times_seen
                    if d.created_at:
                        defect_age_days = max(0, (session.created_at - d.created_at).days)

                tc_dict = {
                    "testcase_id": tc.testcase_code,
                    "display_name": tc.display_name or tc.testcase_code,
                    "rule_id": tc.rule_id,
                    "testcase_name": tc.testcase_name,
                    "status": tc.status,
                    "severity": tc.severity,
                    "criteria": tc.testcase_name,
                    "level": "A",
                    "principle": "N/A",
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
                    "page_url": tc.page_url or session.url,
                    "page_title": tc.page_title or "Page",
                    "defect_id": defect_code,
                    "defect_status": defect_status,
                    "first_seen_run": defect_first_seen,
                    "last_seen_run": defect_last_seen,
                    "fixed_in_run": defect_fixed_in,
                    "reopen_count": defect_reopen_count,
                    "times_seen": defect_times_seen,
                    "age_days": defect_age_days,
                    "input_tokens": tc.input_tokens or 0,
                    "output_tokens": tc.output_tokens or 0,
                    "refined_by": tc.refined_by or ""
                }
                all_tcs.append(tc_dict)

                if tc.status == "FAIL":
                    violations.append(tc_dict)
                elif tc.status == "PASS":
                    passes.append(tc_dict)
                elif tc.status == "NOT_APPLICABLE":
                    not_applicable.append(tc_dict)
                elif tc.status == "MANUAL_REVIEW":
                    manual_review.append(tc_dict)

            # Scanned pages
            pages_scanned = [p.url for p in session.pages] if session.pages else []
            if not pages_scanned:
                pages_scanned = sorted(list({
                    tc.get("page_url") for tc in all_tcs
                    if tc.get("page_url") and tc.get("page_url") not in ("All pages", "N/A")
                }))
            if not pages_scanned:
                pages_scanned = [session.url]

            # Regression summary vs previous run
            prev_session = session.previous_run if session.previous_run_id else None
            score_delta = round(session.score - (prev_session.score if prev_session else 0.0), 1)

            regression_info = {
                "has_previous_run": bool(prev_session),
                "run_number": session.run_number or 1,
                "previous_run_number": prev_session.run_number if prev_session else None,
                "score": session.score,
                "previous_score": prev_session.score if prev_session else 0.0,
                "score_delta": score_delta,
                "defects_new": session.defects_new,
                "defects_fixed": session.defects_fixed,
                "defects_reopened": session.defects_reopened,
                "defects_open": session.defects_open,
                "defects_not_retested": session.defects_not_retested,
            }

            return {
                "task_id": task_id,
                "url": session.url,
                "summary": session.summary or {},
                "testcases": all_tcs,
                "violations": violations,
                "passes": passes,
                "not_applicable": not_applicable,
                "manual_review": manual_review,
                "pages_scanned": pages_scanned,
                "regression": regression_info,
                "session": {
                    "id": str(session.id),
                    "project_id": str(session.project_id),
                    "run_number": session.run_number,
                    "run_type": session.run_type,
                    "score": session.score,
                    "completed_at": session.completed_at.isoformat() if session.completed_at else None
                }
            }

        # 2. Check testcases_fallback (e.g. from orchestrator JSON or caller)
        if testcases_fallback:
            all_tcs = testcases_fallback
            violations = [tc for tc in all_tcs if tc.get("status") == "FAIL"]
            passes = [tc for tc in all_tcs if tc.get("status") == "PASS"]
            not_applicable = [tc for tc in all_tcs if tc.get("status") in ("NOT_APPLICABLE", "N/A")]
            manual_review = [tc for tc in all_tcs if tc.get("status") == "MANUAL_REVIEW"]

            url = session.url if session else (all_tcs[0].get("page_url", "https://example.com") if all_tcs else "https://example.com")
            pages_scanned = sorted(list({
                tc.get("page_url") for tc in all_tcs
                if tc.get("page_url") and tc.get("page_url") not in ("All pages", "N/A")
            }))
            if not pages_scanned:
                pages_scanned = [url]

            summary = (session.summary if session else {}) or {
                "total_violations": len(violations),
                "passes_count": len(passes),
                "accessibility_score": 100 if not violations else max(0, 100 - len(violations) * 5)
            }

            return {
                "task_id": task_id,
                "url": url,
                "summary": summary,
                "testcases": all_tcs,
                "violations": violations,
                "passes": passes,
                "not_applicable": not_applicable,
                "manual_review": manual_review,
                "pages_scanned": pages_scanned,
                "regression": None,
                "session": {
                    "id": str(session.id) if session else "",
                    "project_id": str(session.project_id) if session and session.project_id else "",
                    "run_number": session.run_number if session else 1,
                    "run_type": session.run_type if session else "baseline",
                    "score": session.score if session else 100.0,
                    "completed_at": session.completed_at.isoformat() if session and session.completed_at else None
                } if session else None
            }

        # 3. Fallback to legacy ViolationRecord if session exists in DB
        if session:
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

            return {
                "task_id": task_id,
                "url": session.url,
                "summary": session.summary or {},
                "testcases": [],
                "violations": violations,
                "passes": [],
                "pages_scanned": [session.url],
                "regression": None,
                "session": {
                    "id": str(session.id),
                    "project_id": str(session.project_id),
                    "run_number": session.run_number,
                    "run_type": session.run_type,
                    "score": session.score,
                    "completed_at": session.completed_at.isoformat() if session.completed_at else None
                }
            }

        return None

    def generate_excel_for_task(self, db: Session, task_id: str) -> Optional[bytes]:
        audit_data = self.build_audit_data(db, task_id)
        if not audit_data:
            return None
        return generate_excel_report(audit_data)

    def get_json_report(self, db: Session, task_id: str) -> Optional[Dict[str, Any]]:
        return self.build_audit_data(db, task_id)


report_service = ReportService()
