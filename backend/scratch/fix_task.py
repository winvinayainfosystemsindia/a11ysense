"""
Fix existing task-f3c1c904a7d1 session summary in PostgreSQL from storage testcase report.
"""
import sys
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import json
from common.database.connection import get_session_local
from common.database.models import AuditSession
from common.config import get_audit_storage_path

def fix_task():
    task_id = "task-f3c1c904a7d1"
    reports_dir = get_audit_storage_path(task_id)
    json_path = os.path.join(reports_dir, f"testcase_report_{task_id}.json")
    if not os.path.exists(json_path):
        print(f"File not found: {json_path}")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        testcases = json.load(f)

    db = get_session_local()()
    try:
        session = db.query(AuditSession).filter_by(task_id=task_id).first()
        if session:
            summary = session.summary or {}
            summary["test_cases"] = testcases
            violations = [tc for tc in testcases if tc.get("status") == "FAIL"]
            summary["total_violations"] = len(violations)
            passes = [tc for tc in testcases if tc.get("status") == "PASS"]
            summary["passes_count"] = len(passes)
            if len(testcases) > 0:
                summary["accessibility_score"] = round((len(passes) / len(testcases)) * 100, 1)
            session.summary = summary
            db.commit()
            print(f"Updated session {task_id}: {len(testcases)} testcases ({len(violations)} violations, score={summary['accessibility_score']})")
    finally:
        db.close()

if __name__ == "__main__":
    fix_task()
