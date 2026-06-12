"""
Proxy Router — forwards audit requests to the Agent service and relays status
  POST /start_audit                   — start a new audit (proxied to Agent)
  GET  /task/{task_id}               — poll audit status
  GET  /task/{task_id}/token_usage   — get LLM token consumption
  GET  /task/{task_id}/testcases     — get generated test case report
"""
from typing import Optional
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from common.database import get_db
from common.database.models import User
from common.auth.deps import get_current_user, require_role
from common.schemas.audit import AuditRequest, AuditTask
from app.services.proxy_service import proxy_service

router = APIRouter(tags=["Audit Proxy"])


# ── Routes ─────────────────────────────────────────────────────────────────

@router.post("/start_audit", response_model=AuditTask)
async def start_audit(
    request: AuditRequest,
    project_id: Optional[str] = None,
    current_user: User = Depends(require_role(["Auditor", "Admin"])),
    db: Session = Depends(get_db)
):
    """
    Start a new accessibility audit. Proxies the request to the Agent Service
    with full multi-tenant context headers attached.
    Requires Auditor or Admin role. Enforces credit and plan depth boundaries.
    """
    return await proxy_service.start_audit(request, project_id, current_user, db)


@router.get("/task/{task_id}", response_model=AuditTask)
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Poll the status of an audit task. Enforces organization-level access control."""
    return await proxy_service.get_task_status(task_id, current_user, db)


@router.get("/task/{task_id}/token_usage")
async def get_task_token_usage(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Return LLM token usage for a specific audit task."""
    return await proxy_service.get_task_token_usage(task_id, current_user, db)


@router.get("/task/{task_id}/testcases")
async def get_task_testcases(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Return the generated test case report for a specific audit task."""
    return await proxy_service.get_task_testcases(task_id, current_user, db)


@router.get("/agents/telemetry")
async def get_agents_telemetry(
    current_user: User = Depends(get_current_user)
):
    """Fetch global agent telemetry metrics from Agent Service."""
    return await proxy_service.get_agents_telemetry(current_user)


@router.get("/agents/telemetry/stream")
async def stream_agents_telemetry(
    current_user: User = Depends(get_current_user)
):
    """Proxy global real-time event stream from Agent Service."""
    return proxy_service.stream_agents_telemetry(current_user)


@router.post("/task/{task_id}/stop")
async def stop_audit_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Stop an ongoing audit task."""
    return await proxy_service.stop_audit_task(task_id, current_user, db)


@router.post("/task/{task_id}/pause")
async def pause_audit_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Pause an ongoing audit task."""
    return await proxy_service.pause_audit_task(task_id, current_user, db)


@router.post("/task/{task_id}/resume")
async def resume_audit_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Resume a paused audit task."""
    return await proxy_service.resume_audit_task(task_id, current_user, db)


@router.delete("/task/{task_id}")
async def delete_audit_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an audit session and clean up downstream task progress."""
    return await proxy_service.delete_audit_task(task_id, current_user, db)
