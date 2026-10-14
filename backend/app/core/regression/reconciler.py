"""
Regression Reconciler for A11ySense AI.
Reconciles audit run test cases against project-level persistent defects.
Implements the defect state machine, exact and loose fingerprint matching,
safety rules, and regression counter computation.
"""
from __future__ import annotations

import uuid
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional, Set, Tuple
from sqlalchemy.orm import Session

from common.database.models import Defect, DefectEvent, TestCase, AuditPage, SuccessCriterion, AuditSession
from app.repository.defect_repo import defect_repo


def normalize_url(url: str) -> str:
    """Normalize a URL for reliable comparison across scans."""
    if not url:
        return ""
    clean = url.strip().split("?")[0].split("#")[0].lower().rstrip("/")
    # Strip standard schemes if present
    for prefix in ("https://", "http://"):
        if clean.startswith(prefix):
            clean = clean[len(prefix):]
    return clean


def compute_fingerprint(rule_id: str, html_or_selector: str, page_url: str) -> str:
    """
    Computes exact defect fingerprint:
    sha1(rule_id + normalized_selector_or_html + normalized_page_url)
    """
    norm_rule = (rule_id or "").strip().lower()
    norm_content = " ".join((html_or_selector or "").strip().split())
    norm_url = normalize_url(page_url)
    raw = f"{norm_rule}|{norm_content}|{norm_url}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def compute_loose_fingerprint(rule_id: str, page_url: str, role_or_name: str) -> str:
    """
    Computes loose defect fingerprint for element changes:
    sha1(rule_id + normalized_page_url + element role/name)
    """
    norm_rule = (rule_id or "").strip().lower()
    norm_url = normalize_url(page_url)
    norm_role = (role_or_name or "").strip().lower()
    raw = f"{norm_rule}|{norm_url}|{norm_role}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


class RegressionReconciler:
    """
    Reconciles a run's failing test cases against existing project defects.
    """

    def reconcile_run(
        self,
        db: Session,
        project_id: uuid.UUID,
        session_id: uuid.UUID,
        scanned_pages: List[Dict[str, Any]],
        fail_testcases: List[Dict[str, Any]],
        is_run_successful: bool = True
    ) -> Dict[str, Any]:
        """
        Executes reconciliation for an audit session.
        Returns a dictionary with regression counters and status changes.
        """
        # Load success criteria lookup map
        sc_rows = db.query(SuccessCriterion).all()
        sc_map = {sc.sc_code: sc.id for sc in sc_rows}

        # Load all existing project defects
        existing_defects = defect_repo.get_project_defects_map(db, str(project_id))
        unmatched_defect_ids: Set[uuid.UUID] = {d.id for d in existing_defects.values()}

        # Build scanned URLs set
        scanned_urls: Set[str] = {
            normalize_url(p.get("url", ""))
            for p in scanned_pages
            if p.get("status") in ("scanned", "completed")
        }

        # Track counters
        defects_new = 0
        defects_fixed = 0
        defects_reopened = 0
        defects_open = 0
        defects_not_retested = 0

        matched_defect_ids_in_this_run: Set[uuid.UUID] = set()

        # Process each FAIL test case
        for tc in fail_testcases:
            rule_id = tc.get("rule_id", "Unknown")
            page_url = tc.get("page_url", "")
            raw_html = tc.get("html_snippet") or tc.get("selector") or ""
            role_or_name = tc.get("testcase_name") or tc.get("criteria") or ""

            # 1. Compute fingerprints
            fp = compute_fingerprint(rule_id, raw_html, page_url)
            loose_fp = compute_loose_fingerprint(rule_id, page_url, role_or_name)
            tc["fingerprint"] = fp

            # 2. Match exact fingerprint
            matched_defect: Optional[Defect] = existing_defects.get(fp)

            # 3. Fallback to loose fingerprint against unmatched defects
            if not matched_defect:
                for d in existing_defects.values():
                    if d.id in unmatched_defect_ids and d.loose_fingerprint == loose_fp:
                        matched_defect = d
                        # Update fingerprint to latest markup
                        d.fingerprint = fp
                        break

            # 4. Extract SC ID
            sc_code = ""
            crit = tc.get("criteria", "")
            if crit:
                sc_code = crit.split(" ")[0].strip()
            sc_id = sc_map.get(sc_code)

            if matched_defect:
                matched_defect_ids_in_this_run.add(matched_defect.id)
                unmatched_defect_ids.discard(matched_defect.id)

                # Link testcase
                tc["defect_id_uuid"] = matched_defect.id
                tc["defect_id"] = matched_defect.defect_code

                old_status = matched_defect.status
                new_status = old_status

                # Check severity changes
                tc_sev = tc.get("severity", matched_defect.severity)
                if tc_sev and tc_sev != matched_defect.severity:
                    defect_repo.add_defect_event(
                        db=db,
                        defect_id=matched_defect.id,
                        audit_session_id=session_id,
                        event="severity_changed",
                        from_status=matched_defect.severity,
                        to_status=tc_sev,
                        note=f"Severity updated from {matched_defect.severity} to {tc_sev}"
                    )
                    matched_defect.severity = tc_sev

                # State Machine Transitions
                if old_status in ("WontFix", "FalsePositive"):
                    # Stays suppressed
                    defect_repo.add_defect_event(
                        db=db,
                        defect_id=matched_defect.id,
                        audit_session_id=session_id,
                        event="still_suppressed",
                        from_status=old_status,
                        to_status=old_status,
                        note="Defect detected but is suppressed by user override"
                    )
                elif old_status in ("New", "Open"):
                    new_status = "Open"
                    matched_defect.status = new_status
                    matched_defect.times_seen += 1
                    matched_defect.last_seen_run_id = session_id
                    matched_defect.clean_runs_count = 0
                    defects_open += 1
                    defect_repo.add_defect_event(
                        db=db,
                        defect_id=matched_defect.id,
                        audit_session_id=session_id,
                        event="still_open",
                        from_status=old_status,
                        to_status=new_status,
                        note=f"Observed again in run. Times seen: {matched_defect.times_seen}"
                    )
                elif old_status in ("Fixed", "Closed"):
                    new_status = "Reopened"
                    matched_defect.status = new_status
                    matched_defect.reopen_count += 1
                    matched_defect.times_seen += 1
                    matched_defect.last_seen_run_id = session_id
                    matched_defect.clean_runs_count = 0
                    defects_reopened += 1
                    defect_repo.add_defect_event(
                        db=db,
                        defect_id=matched_defect.id,
                        audit_session_id=session_id,
                        event="reopened",
                        from_status=old_status,
                        to_status=new_status,
                        note=f"Regression detected. Reopened (count: {matched_defect.reopen_count})"
                    )
                elif old_status == "Reopened":
                    matched_defect.times_seen += 1
                    matched_defect.last_seen_run_id = session_id
                    defects_reopened += 1
                    defect_repo.add_defect_event(
                        db=db,
                        defect_id=matched_defect.id,
                        audit_session_id=session_id,
                        event="still_open",
                        from_status=old_status,
                        to_status=old_status,
                        note=f"Still failing after reopen (times seen: {matched_defect.times_seen})"
                    )

                # Update latest evidence
                matched_defect.code_before = tc.get("code_before") or raw_html
                matched_defect.code_after = tc.get("code_after") or ""
                matched_defect.fix_steps = tc.get("fix_steps") or []
                matched_defect.verify_steps = tc.get("verify_steps") or []
                matched_defect.false_positive_note = tc.get("false_positive_note") or ""

            else:
                # Brand new defect!
                defect_code = defect_repo.get_next_defect_code(db, str(project_id))
                new_defect_data = {
                    "project_id": project_id,
                    "defect_code": defect_code,
                    "fingerprint": fp,
                    "loose_fingerprint": loose_fp,
                    "rule_id": rule_id,
                    "success_criterion_id": sc_id,
                    "page_url": page_url,
                    "title": role_or_name or rule_id,
                    "severity": tc.get("severity", "Moderate"),
                    "fix_steps": tc.get("fix_steps") or [],
                    "code_before": tc.get("code_before") or raw_html,
                    "code_after": tc.get("code_after") or "",
                    "verify_steps": tc.get("verify_steps") or [],
                    "false_positive_note": tc.get("false_positive_note") or "",
                    "status": "New",
                    "first_seen_run_id": session_id,
                    "last_seen_run_id": session_id,
                    "times_seen": 1,
                    "reopen_count": 0,
                    "clean_runs_count": 0
                }
                new_defect = defect_repo.create_defect(db, new_defect_data)
                existing_defects[fp] = new_defect
                matched_defect_ids_in_this_run.add(new_defect.id)

                # Link testcase
                tc["defect_id_uuid"] = new_defect.id
                tc["defect_id"] = new_defect.defect_code

                defects_new += 1
                defect_repo.add_defect_event(
                    db=db,
                    defect_id=new_defect.id,
                    audit_session_id=session_id,
                    event="detected",
                    from_status=None,
                    to_status="New",
                    note="First detected by audit scan"
                )

        # 5. Handle Unmatched Defects (defects absent in this run)
        for d in existing_defects.values():
            if d.id in matched_defect_ids_in_this_run:
                continue

            defect_page_norm = normalize_url(d.page_url)
            page_was_scanned = defect_page_norm in scanned_urls

            if not page_was_scanned or not is_run_successful:
                # Safety rule: Page not scanned or run stopped/failed -> Not retested
                defects_not_retested += 1
            else:
                # Page was successfully scanned and this defect was NOT found
                if d.status in ("WontFix", "FalsePositive"):
                    continue
                elif d.status in ("New", "Open", "Reopened"):
                    old_st = d.status
                    d.status = "Fixed"
                    d.fixed_in_run_id = session_id
                    d.clean_runs_count = 1
                    d.resolved_at = datetime.utcnow()
                    defects_fixed += 1
                    defect_repo.add_defect_event(
                        db=db,
                        defect_id=d.id,
                        audit_session_id=session_id,
                        event="auto_fixed",
                        from_status=old_st,
                        to_status="Fixed",
                        note="Verified absent during full page scan"
                    )
                elif d.status == "Fixed":
                    d.clean_runs_count += 1
                    if d.clean_runs_count >= 2:
                        d.status = "Closed"
                        defect_repo.add_defect_event(
                            db=db,
                            defect_id=d.id,
                            audit_session_id=session_id,
                            event="closed",
                            from_status="Fixed",
                            to_status="Closed",
                            note="Closed automatically after 2 consecutive clean runs"
                        )

        db.flush()

        return {
            "defects_new": defects_new,
            "defects_fixed": defects_fixed,
            "defects_reopened": defects_reopened,
            "defects_open": defects_open,
            "defects_not_retested": defects_not_retested
        }


reconciler = RegressionReconciler()
