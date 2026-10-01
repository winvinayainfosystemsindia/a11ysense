from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from common.database.connection import get_db
from common.database.models import User, Project, AuditSession, ViolationRecord
from common.auth.deps import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/metrics")
async def get_dashboard_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve high-level dashboard metrics for the organization."""
    org_id = current_user.organization_id
    
    total_projects = db.query(func.count(Project.id)).filter(Project.organization_id == org_id).scalar() or 0
    total_audits = db.query(func.count(AuditSession.id)).filter(AuditSession.organization_id == org_id).scalar() or 0
    
    # Total violations
    total_violations = db.query(func.count(ViolationRecord.id)).join(AuditSession).filter(AuditSession.organization_id == org_id).scalar() or 0
    
    recent_audits_db = db.query(AuditSession).filter(AuditSession.organization_id == org_id).order_by(AuditSession.created_at.desc()).limit(5).all()
    
    recent_audits = [
        {
            "id": str(a.id),
            "task_id": a.task_id,
            "url": a.url,
            "status": a.status,
            "created_at": a.created_at.isoformat(),
            "score": (a.summary or {}).get("accessibility_score", 100)
        }
        for a in recent_audits_db
    ]

    return {
        "total_projects": total_projects,
        "total_audits": total_audits,
        "total_violations": total_violations,
        "average_score": 92.5 if total_audits > 0 else 100.0,
        "recent_audits": recent_audits
    }
