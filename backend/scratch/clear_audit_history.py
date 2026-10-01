"""
Utility script to clear all audit history records from the database and storage.
"""
import sys
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from common.database.connection import get_session_local
from common.database.models import AuditSession, ViolationRecord, AuditProgress, CrawlProgress

def clear_audit_history():
    db = get_session_local()()
    try:
        num_violations = db.query(ViolationRecord).delete()
        num_sessions = db.query(AuditSession).delete()
        num_audit_progress = db.query(AuditProgress).delete()
        num_crawl_progress = db.query(CrawlProgress).delete()
        db.commit()
        print(f"Successfully deleted:\n- {num_sessions} audit sessions\n- {num_violations} violation records\n- {num_audit_progress} audit progress records\n- {num_crawl_progress} crawl progress records")
    except Exception as e:
        db.rollback()
        print(f"Error clearing audit history: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    clear_audit_history()
