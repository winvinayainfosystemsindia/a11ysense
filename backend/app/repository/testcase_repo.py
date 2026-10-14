import uuid
import logging
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from common.database.models import TestCase, AuditPage, RunCriterionResult, SuccessCriterion

logger = logging.getLogger(__name__)


class TestCaseRepository:
    def bulk_create_pages(
        self,
        db: Session,
        session_id: uuid.UUID,
        pages_data: List[Dict[str, Any]]
    ) -> Dict[str, AuditPage]:
        """
        Inserts AuditPage rows for a session and returns a dictionary mapped by normalized_url.
        """
        pages_map = {}
        for p in pages_data:
            raw_url = p.get("url", "")
            norm_url = p.get("normalized_url") or raw_url.strip().lower().rstrip("/")
            if not norm_url:
                continue

            existing = db.query(AuditPage).filter_by(
                audit_session_id=session_id,
                url=raw_url
            ).first()

            if not existing:
                page_rec = AuditPage(
                    audit_session_id=session_id,
                    url=raw_url,
                    normalized_url=norm_url,
                    title=p.get("title", ""),
                    depth=p.get("depth", 1),
                    status=p.get("status", "scanned")
                )
                db.add(page_rec)
                pages_map[norm_url] = page_rec
                pages_map[raw_url] = page_rec
            else:
                pages_map[norm_url] = existing
                pages_map[raw_url] = existing

        db.flush()
        return pages_map

    def bulk_create_testcases(
        self,
        db: Session,
        testcase_records: List[Dict[str, Any]],
        batch_size: int = 500
    ) -> List[TestCase]:
        """
        Bulk inserts TestCase rows in chunks.
        """
        created = []
        for i in range(0, len(testcase_records), batch_size):
            chunk = testcase_records[i:i + batch_size]
            instances = []
            for tc_data in chunk:
                tc = TestCase(**tc_data)
                instances.append(tc)
            db.add_all(instances)
            db.flush()
            created.extend(instances)
        return created

    def get_testcases_by_session(
        self,
        db: Session,
        session_id: uuid.UUID,
        status: Optional[str] = None,
        rule_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[TestCase], int]:
        query = db.query(TestCase).filter(TestCase.audit_session_id == session_id)
        if status:
            query = query.filter(TestCase.status == status.upper())
        if rule_id:
            query = query.filter(TestCase.rule_id == rule_id)

        total = query.count()
        results = query.order_by(TestCase.testcase_code.asc()).offset(offset).limit(limit).all()
        return results, total

    def get_all_testcases_by_session(
        self,
        db: Session,
        session_id: uuid.UUID
    ) -> List[TestCase]:
        return (
            db.query(TestCase)
            .filter(TestCase.audit_session_id == session_id)
            .order_by(TestCase.testcase_code.asc())
            .all()
        )

    def count_testcases_by_status(
        self,
        db: Session,
        session_id: uuid.UUID
    ) -> Dict[str, int]:
        counts = (
            db.query(TestCase.status, func.count(TestCase.id))
            .filter(TestCase.audit_session_id == session_id)
            .group_by(TestCase.status)
            .all()
        )
        result = {"PASS": 0, "FAIL": 0, "NOT_APPLICABLE": 0, "MANUAL_REVIEW": 0}
        for st, cnt in counts:
            result[st] = cnt
        return result

    def bulk_create_criterion_results(
        self,
        db: Session,
        session_id: uuid.UUID,
        criterion_results: List[Dict[str, Any]]
    ) -> List[RunCriterionResult]:
        created = []
        for cr in criterion_results:
            rec = RunCriterionResult(
                audit_session_id=session_id,
                success_criterion_id=cr["success_criterion_id"],
                status=cr["status"],
                pass_count=cr.get("pass_count", 0),
                fail_count=cr.get("fail_count", 0)
            )
            db.add(rec)
            created.append(rec)
        db.flush()
        return created

    def get_criterion_results_by_session(
        self,
        db: Session,
        session_id: uuid.UUID
    ) -> List[RunCriterionResult]:
        return (
            db.query(RunCriterionResult)
            .filter(RunCriterionResult.audit_session_id == session_id)
            .all()
        )


testcase_repo = TestCaseRepository()
