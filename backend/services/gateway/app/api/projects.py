"""
Projects Router — GET /api/projects, POST /api/projects
"""
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from common.database import get_db
from common.database.models import User, Project
from common.auth.deps import get_current_user, require_role
from app.schemas.projects import ProjectCreate, ProjectResponse

router = APIRouter(prefix="/api/projects", tags=["Projects"])


# ── Routes ─────────────────────────────────────────────────────────────────

@router.get("", response_model=List[ProjectResponse])
async def list_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all projects belonging to the current user's organization."""
    projects = (
        db.query(Project)
        .filter_by(organization_id=current_user.organization_id)
        .order_by(Project.created_at.desc())
        .all()
    )
    return projects


@router.post("", response_model=ProjectResponse)
async def create_project(
    req: ProjectCreate,
    current_user: User = Depends(require_role(["Auditor", "Admin"])),
    db: Session = Depends(get_db)
):
    """Create a new project under the current user's organization. Requires Auditor or Admin role."""
    new_project = Project(
        name=req.name,
        organization_id=current_user.organization_id
    )
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    return new_project
