"""
Projects Router — GET /api/projects, POST /api/projects
"""
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from common.database import get_db
from common.database.models import User
from common.auth.deps import get_current_user, require_role
from app.schemas.projects import ProjectCreate, ProjectResponse
from app.services.project_service import project_service

router = APIRouter(prefix="/api/projects", tags=["Projects"])


# ── Routes ─────────────────────────────────────────────────────────────────

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
    """Create a new project under the current user's organization. Requires Auditor or Admin role."""
    return project_service.create_project(req, current_user, db)
