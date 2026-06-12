from datetime import datetime
from sqlalchemy.orm import Session
from common.database.models import AuditSession

class DashboardRepository:
    def list_audits(self, db: Session, org_id: str) -> list[AuditSession]:
        return (
            db.query(AuditSession)
            .filter_by(organization_id=org_id)
            .order_by(AuditSession.created_at.desc())
            .all()
        )

    def get_sessions_by_timerange(
        self,
        db: Session,
        org_id: str,
        since: datetime | None = None
    ) -> list[AuditSession]:
        query = db.query(AuditSession).filter_by(organization_id=org_id)
        if since:
            query = query.filter(AuditSession.timestamp >= since)
        return query.order_by(AuditSession.created_at.desc()).all()

    def get_completed_sessions_by_timerange(
        self,
        db: Session,
        org_id: str,
        since: datetime | None = None
    ) -> list[AuditSession]:
        query = db.query(AuditSession).filter(
            AuditSession.organization_id == org_id,
            AuditSession.status == "completed"
        )
        if since:
            query = query.filter(AuditSession.timestamp >= since)
        return query.order_by(AuditSession.timestamp.asc()).all()

dashboard_repo = DashboardRepository()
