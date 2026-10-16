"""
Regression Reconciler for A11ySense AI.
Reconciles audit run test cases against project-level persistent defects.
Implements the defect state machine, exact and loose fingerprint matching,
group-level matching for live dynamic content, safety rules, and regression counter computation.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Set, Tuple
from sqlalchemy.orm import Session

from common.database.models import Defect, DefectEvent, TestCase, AuditPage, SuccessCriterion, AuditSession
from app.repository.defect_repo import defect_repo
from app.core.regression.fingerprint import (
    normalize_url,
    compute_fingerprint,
    compute_loose_fingerprint,
    normalize_dynamic_text,
    fingerprint_batch,
    FingerprintResult,
)
from app.core.regression.matcher import MatchItem, match_groups, MatchResult


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
        p_uuid = uuid.UUID(str(project_id)) if isinstance(project_id, str) else project_id
        existing_defects_list: List[Defect] = db.query(Defect).filter(Defect.project_id == p_uuid).all()

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

        # Step 1: Batch fingerprint current fail testcases
        cur_recs = [
            {
                "rule_id": tc.get("rule_id", "Unknown"),
                "html": tc.get("html_snippet") or tc.get("selector") or "",
                "page_url": tc.get("page_url", ""),
                "criteria": tc.get("criteria", ""),
                "landmark": tc.get("landmark", "")
            }
            for tc in fail_testcases
        ]
        cur_fp_results = fingerprint_batch(cur_recs) if cur_recs else []
        for tc, fres in zip(fail_testcases, cur_fp_results):
            tc["fingerprint"] = f"{fres.fp}:{fres.occurrence}" if fres.occurrence > 0 else fres.fp
            tc["_group_fp"] = fres.fp
            tc["_occurrence"] = fres.occurrence
            tc["_dynamic"] = fres.dynamic
            role_or_name = tc.get("testcase_name") or tc.get("criteria") or ""
            tc["loose_fingerprint"] = compute_loose_fingerprint(tc.get("rule_id", "Unknown"), tc.get("page_url", ""), role_or_name)

        # Step 2: Back-compat & Batch fingerprint existing project defects
        # Compute new stable fingerprint from stored code_before / snippet at comparison time
        prev_recs = [
            {
                "rule_id": d.rule_id,
                "html": d.code_before or d.title or "",
                "page_url": d.page_url,
                "criteria": "",
            }
            for d in existing_defects_list
        ]
        prev_fp_results = fingerprint_batch(prev_recs) if prev_recs else []

        # Prepare MatchItems for existing defects
        # Priority: Open/New/Reopened (0), WontFix/FalsePositive (1), Fixed (2), Closed (3)
        status_prio = {"Open": 0, "New": 0, "Reopened": 0, "FalsePositive": 1, "WontFix": 1, "Fixed": 2, "Closed": 3}
        prev_items: List[MatchItem] = []
        for d, fres in zip(existing_defects_list, prev_fp_results):
            expected_fp = f"{fres.fp}:{fres.occurrence}" if fres.occurrence > 0 else fres.fp
            # Keep stored fingerprint in sync with stable identity
            if d.fingerprint != expected_fp:
                d.fingerprint = expected_fp
            d.loose_fingerprint = compute_loose_fingerprint(d.rule_id, d.page_url, d.title or "")
            prev_items.append(
                MatchItem(
                    ref=d,
                    fp=fres.fp,
                    dynamic=fres.dynamic,
                    priority=status_prio.get(d.status, 0),
                    order=fres.occurrence
                )
            )

        # Prepare MatchItems for current fail testcases
        cur_items: List[MatchItem] = [
            MatchItem(
                ref=tc,
                fp=fres.fp,
                dynamic=fres.dynamic,
                order=fres.occurrence
            )
            for tc, fres in zip(fail_testcases, cur_fp_results)
        ]

        # Step 3: Match groups (counts decide new/fixed/open per group)
        match_result = match_groups(prev_items, cur_items)

        # Fallback loose matching for remaining unmatched items
        remaining_new = list(match_result.new)
        remaining_unmatched_prev = list(match_result.unmatched_prev)
        unmatched_prev_set = set(remaining_unmatched_prev)

        pairs = list(match_result.pairs)
        final_new: List[MatchItem] = []

        for c_item in remaining_new:
            tc = c_item.ref
            loose_fp = tc.get("loose_fingerprint")
            matched_p = None
            for p_item in remaining_unmatched_prev:
                if p_item in unmatched_prev_set:
                    d = p_item.ref
                    if d.loose_fingerprint == loose_fp or compute_loose_fingerprint(d.rule_id, d.page_url, d.title) == loose_fp:
                        matched_p = p_item
                        break
            if matched_p:
                pairs.append((matched_p, c_item))
                unmatched_prev_set.discard(matched_p)
                remaining_unmatched_prev.remove(matched_p)
            else:
                final_new.append(c_item)

        final_unmatched_prev = [p for p in match_result.unmatched_prev if p in unmatched_prev_set]

        # Step 4: Process matched pairs (Still Open, Reopened, etc.)
        for p_item, c_item in pairs:
            matched_defect: Defect = p_item.ref
            tc: Dict[str, Any] = c_item.ref

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

            # Update latest evidence and fingerprint
            if tc.get("fingerprint") and matched_defect.fingerprint != tc.get("fingerprint"):
                matched_defect.fingerprint = tc.get("fingerprint")
            raw_html = tc.get("html_snippet") or tc.get("selector") or ""
            matched_defect.code_before = tc.get("code_before") or raw_html
            matched_defect.code_after = tc.get("code_after") or ""
            matched_defect.fix_steps = tc.get("fix_steps") or []
            matched_defect.verify_steps = tc.get("verify_steps") or []
            matched_defect.false_positive_note = tc.get("false_positive_note") or ""

        # Step 5: Process brand new defects
        for c_item in final_new:
            tc: Dict[str, Any] = c_item.ref
            rule_id = tc.get("rule_id", "Unknown")
            page_url = tc.get("page_url", "")
            raw_html = tc.get("html_snippet") or tc.get("selector") or ""
            role_or_name = tc.get("testcase_name") or tc.get("criteria") or ""
            fp = tc.get("fingerprint") or c_item.fp
            loose_fp = tc.get("loose_fingerprint") or compute_loose_fingerprint(rule_id, page_url, role_or_name)

            sc_code = ""
            crit = tc.get("criteria", "")
            if crit:
                sc_code = crit.split(" ")[0].strip()
            sc_id = sc_map.get(sc_code)

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

        # Step 6: Process unmatched defects (Fixed / Not Retested / Closed)
        for p_item in final_unmatched_prev:
            d: Defect = p_item.ref
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
            "defects_not_retested": defects_not_retested,
            "dynamic_groups_matched": match_result.dynamic_groups_matched
        }


reconciler = RegressionReconciler()
