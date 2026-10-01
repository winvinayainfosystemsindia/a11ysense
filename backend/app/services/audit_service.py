"""
Audit Service handling audit lifecycle, progress queries, and session management.
"""
import uuid
import logging
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from common.database.models import AuditProgress, AuditSession, User
from common.schemas.audit import AuditRequest
from backend.app.task_queue import task_queue
from backend.app.core.audit.orchestrator import AuditOrchestrator

logger = logging.getLogger(__name__)

class AuditService:
    def __init__(self):
        self.orchestrator = AuditOrchestrator()

    def start_audit(self, db: Session, req: AuditRequest, current_user: User) -> str:
        task_id = f"task-{uuid.uuid4().hex[:12]}"
        progress = AuditProgress(
            task_id=task_id,
            url=req.url,
            status="processing",
            depth=req.depth
        )
        db.add(progress)
        db.commit()

        task_queue.run_task(
            self.orchestrator.run_in_memory_audit_flow,
            task_id,
            req,
            str(current_user.organization_id)
        )
        return task_id

    def get_audit_progress(self, db: Session, task_id: str) -> Optional[AuditProgress]:
        return db.query(AuditProgress).filter(AuditProgress.task_id == task_id).first()

    def list_audit_sessions(self, db: Session, org_id: uuid.UUID) -> List[AuditSession]:
        return db.query(AuditSession).filter(AuditSession.organization_id == org_id).order_by(AuditSession.created_at.desc()).all()

audit_service = AuditService()
