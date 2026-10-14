import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from common.database.connection import get_db
from common.database.models import User
from common.auth.deps import get_current_user, require_role
from common.schemas.projects import ProjectCreate, ProjectResponse
from backend.app.services.project_service import project_service
from app.repository.project_repo import project_repo
from app.repository.defect_repo import defect_repo

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
    """Create a new project under current user's organization."""
    return project_service.create_project(req, current_user, db)


@router.get("/{project_id}")
async def get_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get project details with latest run metrics."""
    project = project_repo.get_project(db, project_id)
    if not project or project.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Project not found")

    latest_run = project_repo.get_latest_completed_run(db, project_id)
    return {
        "id": str(project.id),
        "name": project.name,
        "description": project.description,
        "status": project.status,
        "project_type": project.project_type,
        "base_url": project.base_url,
        "created_at": project.created_at.isoformat() if project.created_at else None,
        "latest_score": latest_run.score if latest_run else None,
        "latest_run_number": latest_run.run_number if latest_run else None,
        "total_runs": len(project.audit_sessions) if project.audit_sessions else 0
    }


@router.get("/{project_id}/runs")
async def list_project_runs(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all audit runs for a project with regression counters and score deltas."""
    project = project_repo.get_project(db, project_id)
    if not project or project.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Project not found")

    runs = project_repo.get_project_runs(db, project_id)
    result = []
    for r in runs:
        prev = r.previous_run if r.previous_run_id else None
        score_delta = round(r.score - (prev.score if prev else 0.0), 1) if prev else 0.0
        result.append({
            "id": str(r.id),
            "task_id": r.task_id,
            "run_number": r.run_number,
            "run_type": r.run_type,
            "previous_run_id": str(r.previous_run_id) if r.previous_run_id else None,
            "previous_run_number": prev.run_number if prev else None,
            "url": r.url,
            "status": r.status,
            "score": r.score,
            "score_delta": score_delta,
            "total_testcases": r.total_testcases,
            "fail": r.fail_count,
            "pass": r.pass_count,
            "na": r.na_count,
            "manual": r.manual_count,
            "defects_new": r.defects_new,
            "defects_fixed": r.defects_fixed,
            "defects_reopened": r.defects_reopened,
            "defects_open": r.defects_open,
            "defects_not_retested": r.defects_not_retested,
            "scope_fingerprint": r.scope_fingerprint,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "completed_at": r.completed_at.isoformat() if r.completed_at else None,
        })
    return result


@router.get("/{project_id}/trend")
async def get_project_trend(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Return historical trend data (score and defect evolution across runs)."""
    project = project_repo.get_project(db, project_id)
    if not project or project.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Project not found")

    return project_repo.get_project_trend(db, project_id)


@router.get("/{project_id}/defects")
async def list_project_defects(
    project_id: str,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List persistent defects for a project with status and severity filters."""
    project = project_repo.get_project(db, project_id)
    if not project or project.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Project not found")

    defects, total = defect_repo.get_defects_by_project(
        db, project_id, status=status, severity=severity, limit=limit, offset=offset
    )
    items = []
    for d in defects:
        first_run = d.first_seen_run.run_number if d.first_seen_run else 1
        last_run = d.last_seen_run.run_number if d.last_seen_run else None
        fixed_run = d.fixed_in_run.run_number if d.fixed_in_run else None
        age_days = (datetime.utcnow() - d.created_at).days if d.created_at else 0
        items.append({
            "id": str(d.id),
            "defect_code": d.defect_code,
            "title": d.title,
            "rule_id": d.rule_id,
            "page_url": d.page_url,
            "severity": d.severity,
            "status": d.status,
            "first_seen_run": first_run,
            "last_seen_run": last_run,
            "fixed_in_run": fixed_run,
            "reopen_count": d.reopen_count,
            "times_seen": d.times_seen,
            "age_days": age_days,
            "notes": d.notes,
            "suppressed_reason": d.suppressed_reason,
            "created_at": d.created_at.isoformat() if d.created_at else None,
            "updated_at": d.updated_at.isoformat() if d.updated_at else None
        })

    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset
    }
