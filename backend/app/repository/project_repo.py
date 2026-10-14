import uuid
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from common.database.models import Project, AuditSession, Defect


class ProjectRepository:
    def get_project(self, db: Session, project_id: str) -> Optional[Project]:
        try:
            p_uuid = uuid.UUID(project_id) if isinstance(project_id, str) else project_id
            return db.query(Project).filter(Project.id == p_uuid).first()
        except (ValueError, TypeError):
            return None

    def get_or_create_default_project(self, db: Session, org_id: str) -> Project:
        o_uuid = uuid.UUID(org_id) if isinstance(org_id, str) else org_id
        project = db.query(Project).filter_by(
            name="Default Project",
            organization_id=o_uuid
        ).first()
        if not project:
            project = Project(
                name="Default Project",
                project_type="web_page",
                status="active",
                organization_id=o_uuid
            )
            db.add(project)
            db.commit()
            db.refresh(project)
        return project

    def list_projects(self, db: Session, org_id: str) -> List[Project]:
        try:
            o_uuid = uuid.UUID(org_id) if isinstance(org_id, str) else org_id
            return (
                db.query(Project)
                .filter_by(organization_id=o_uuid)
                .order_by(Project.created_at.desc())
                .all()
            )
        except (ValueError, TypeError):
            return []

    def create_project(
        self,
        db: Session,
        name: str,
        org_id: str,
        description: Optional[str] = None,
        project_type: str = "web_page",
        base_url: Optional[str] = None
    ) -> Project:
        o_uuid = uuid.UUID(org_id) if isinstance(org_id, str) else org_id
        new_project = Project(
            name=name,
            description=description,
            project_type=project_type,
            base_url=base_url,
            status="active",
            organization_id=o_uuid
        )
        db.add(new_project)
        db.commit()
        db.refresh(new_project)
        return new_project

    def update_project(self, db: Session, project_id: str, **kwargs) -> Optional[Project]:
        project = self.get_project(db, project_id)
        if not project:
            return None
        for key, value in kwargs.items():
            if hasattr(project, key):
                setattr(project, key, value)
        db.commit()
        db.refresh(project)
        return project

    def delete_project(self, db: Session, project_id: str) -> bool:
        project = self.get_project(db, project_id)
        if not project:
            return False
        db.delete(project)
        db.commit()
        return True

    def get_project_runs(self, db: Session, project_id: str) -> List[AuditSession]:
        p_uuid = uuid.UUID(project_id) if isinstance(project_id, str) else project_id
        return (
            db.query(AuditSession)
            .filter(AuditSession.project_id == p_uuid)
            .order_by(desc(AuditSession.run_number), desc(AuditSession.created_at))
            .all()
        )

    def get_latest_completed_run(self, db: Session, project_id: str) -> Optional[AuditSession]:
        p_uuid = uuid.UUID(project_id) if isinstance(project_id, str) else project_id
        return (
            db.query(AuditSession)
            .filter(
                AuditSession.project_id == p_uuid,
                AuditSession.status == "completed"
            )
            .order_by(desc(AuditSession.run_number), desc(AuditSession.completed_at))
            .first()
        )

    def get_next_run_number(self, db: Session, project_id: str) -> int:
        p_uuid = uuid.UUID(project_id) if isinstance(project_id, str) else project_id
        max_run = (
            db.query(func.max(AuditSession.run_number))
            .filter(AuditSession.project_id == p_uuid)
            .scalar()
        )
        return (max_run or 0) + 1

    def get_project_trend(self, db: Session, project_id: str) -> List[Dict[str, Any]]:
        """Returns run-by-run trend data for score, open defects, fixed defects, and new defects."""
        runs = self.get_project_runs(db, project_id)
        # Sort chronologically for trend charts
        chronological_runs = sorted(
            [r for r in runs if r.status in ("completed", "stopped")],
            key=lambda x: (x.run_number or 0, x.created_at)
        )
        trend = []
        for r in chronological_runs:
            trend.append({
                "task_id": r.task_id,
                "run_number": r.run_number,
                "run_type": r.run_type,
                "score": r.score,
                "status": r.status,
                "defects_open": r.defects_open,
                "defects_new": r.defects_new,
                "defects_fixed": r.defects_fixed,
                "defects_reopened": r.defects_reopened,
                "total_testcases": r.total_testcases,
                "completed_at": r.completed_at.isoformat() if r.completed_at else (r.created_at.isoformat() if r.created_at else None)
            })
        return trend


project_repo = ProjectRepository()
