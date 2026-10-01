from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from common.database.connection import get_db
from common.database.models import User
from common.auth.deps import get_current_user, require_role
from common.schemas.projects import ProjectCreate, ProjectResponse
from backend.app.services.project_service import project_service

router = APIRouter(prefix="/api/projects", tags=["Projects"])

@router.get("", response_model=List[ProjectResponse])
async def list_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all projects belonging to the current user's organization."""
    return project_service.list_projects(current_user, db)

@router.post("", response_model=ProjectResponse)
async def create_project(
    req: ProjectCreate,
    current_user: User = Depends(require_role(["Auditor", "Admin"])),
    db: Session = Depends(get_db)
):
    """Create a new project under current user's organization with Web Page or Web Application target type."""
    return project_service.create_project(req, current_user, db)
