from typing import List
from sqlalchemy.orm import Session
from common.database.models import User, Project
from common.schemas.projects import ProjectCreate, ProjectResponse

class ProjectService:
    def list_projects(self, current_user: User, db: Session) -> List[ProjectResponse]:
        projects = db.query(Project).filter(Project.organization_id == current_user.organization_id).order_by(Project.created_at.desc()).all()
        return [ProjectResponse.model_validate(p) for p in projects]

    def create_project(self, req: ProjectCreate, current_user: User, db: Session) -> ProjectResponse:
        project = Project(
            name=req.name,
            project_type=req.project_type,
            base_url=req.base_url,
            organization_id=current_user.organization_id
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        return ProjectResponse.model_validate(project)

project_service = ProjectService()
