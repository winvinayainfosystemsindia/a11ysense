from sqlalchemy.orm import Session
from common.database.models import User, Project
from app.repository.project_repo import project_repo
from app.schemas.projects import ProjectCreate

class ProjectService:
    def list_projects(self, current_user: User, db: Session) -> list[Project]:
        return project_repo.list_projects(db, current_user.organization_id)

    def create_project(self, req: ProjectCreate, current_user: User, db: Session) -> Project:
        return project_repo.create_project(db, req.name, current_user.organization_id)

project_service = ProjectService()
