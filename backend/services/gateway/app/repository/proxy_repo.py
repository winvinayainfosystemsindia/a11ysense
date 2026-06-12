from sqlalchemy.orm import Session
from common.database.models import Project, AuditSession

class ProxyRepository:
    def get_default_project_by_org(self, db: Session, org_id: str) -> Project | None:
        return db.query(Project).filter_by(
            name="Default Project",
            organization_id=org_id
        ).first()

    def get_session_by_task_id(self, db: Session, task_id: str) -> AuditSession | None:
        return db.query(AuditSession).filter_by(task_id=task_id).first()

    def update_session_status(self, db: Session, session: AuditSession, status: str) -> None:
        session.status = status
        db.commit()

    def delete_session(self, db: Session, session: AuditSession) -> None:
        db.delete(session)
        db.commit()

proxy_repo = ProxyRepository()
