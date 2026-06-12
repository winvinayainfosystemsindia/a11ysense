from sqlalchemy.orm import Session
from common.database.models import Project

class ProjectRepository:
    def list_projects(self, db: Session, org_id: str) -> list[Project]:
        return (
            db.query(Project)
            .filter_by(organization_id=org_id)
            .order_by(Project.created_at.desc())
            .all()
        )

    def create_project(self, db: Session, name: str, org_id: str) -> Project:
        new_project = Project(
            name=name,
            organization_id=org_id
        )
        db.add(new_project)
        db.commit()
        db.refresh(new_project)
        return new_project

project_repo = ProjectRepository()
