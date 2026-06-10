"""
Proxy Router — forwards audit requests to the Agent service and relays status
  POST /start_audit                   — start a new audit (proxied to Agent)
  GET  /task/{task_id}               — poll audit status
  GET  /task/{task_id}/token_usage   — get LLM token consumption
  GET  /task/{task_id}/testcases     — get generated test case report
"""
import os
import logging
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from common.database import get_db
from common.database.connection import get_session_local
from common.database.models import User, Project, AuditSession
from common.auth.deps import get_current_user, require_role
from common.schemas.audit import AuditRequest, AuditTask
from common.utils.correlation import get_correlation_headers

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Audit Proxy"])

from common.config import get_service_url
AGENT_SERVICE_URL = get_service_url("AGENT_SERVICE_URL", "http://agent:8001", "http://localhost:8001")


# ── Helper ─────────────────────────────────────────────────────────────────

def _build_context_headers(current_user: User, project_id: Optional[str] = None) -> dict:
    """Build downstream context propagation headers from the authenticated user."""
    headers = get_correlation_headers()
    headers["X-User-ID"] = str(current_user.id)
    headers["X-Organization-ID"] = str(current_user.organization_id)
    headers["X-User-Role"] = str(current_user.role)
    if project_id:
        headers["X-Project-ID"] = str(project_id)
    return headers


def _resolve_default_project_id(current_user: User) -> Optional[str]:
    """Look up the Default Project ID for the user's organization."""
    db = get_session_local()()
    try:
        proj = db.query(Project).filter_by(
            name="Default Project",
            organization_id=current_user.organization_id
        ).first()
        return str(proj.id) if proj else None
    finally:
        db.close()


def _assert_session_ownership(session: Optional[AuditSession], current_user: User) -> None:
    """Raise 403 if the audit session belongs to a different organization."""
    if session and session.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=403,
            detail="Access denied. Audit session belongs to another workspace."
        )


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
    from common.billing.billing_manager import billing_manager

    # 1. Enforce subscription crawl depth boundaries
    org_id = current_user.organization_id
    billing_manager.check_feature_access(db, org_id, "max_depth", request.depth)

    # 2. Enforce credit balance boundaries (minimum 10 to start)
    if not billing_manager.has_sufficient_credits(db, org_id, minimum_required=10):
        raise HTTPException(
            status_code=402,
            detail="Insufficient credits. A minimum of 10 credits is required to initiate an audit scan."
        )

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            audit_data = request.model_dump(mode="json")

            headers = _build_context_headers(current_user, project_id)

            # Fall back to the Default Project if no project_id was provided
            if not project_id:
                default_proj_id = _resolve_default_project_id(current_user)
                if default_proj_id:
                    headers["X-Project-ID"] = default_proj_id

            response = await client.post(
                f"{AGENT_SERVICE_URL}/audit",
                json=audit_data,
                headers=headers
            )
            response.raise_for_status()
            return AuditTask(**response.json())
        except httpx.HTTPStatusError as hse:
            # Relay details downstream if any microservice raises error
            detail = hse.response.text
            try:
                detail = hse.response.json().get("detail", detail)
            except Exception:
                pass
            raise HTTPException(status_code=hse.response.status_code, detail=detail)
        except HTTPException as he:
            raise he
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@router.get("/task/{task_id}", response_model=AuditTask)
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Poll the status of an audit task. Enforces organization-level access control."""
    session = db.query(AuditSession).filter_by(task_id=task_id).first()
    _assert_session_ownership(session, current_user)

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            headers = _build_context_headers(current_user)
            response = await client.get(
                f"{AGENT_SERVICE_URL}/status/{task_id}",
                headers=headers
            )
            response.raise_for_status()
            return AuditTask(**response.json())
        except Exception as e:
            logger.exception(f"Error fetching task status for task {task_id}")
            raise HTTPException(status_code=500, detail=str(e))


@router.get("/task/{task_id}/token_usage")
async def get_task_token_usage(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Return LLM token usage for a specific audit task."""
    session = db.query(AuditSession).filter_by(task_id=task_id).first()
    _assert_session_ownership(session, current_user)

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            headers = _build_context_headers(current_user)
            response = await client.get(
                f"{AGENT_SERVICE_URL}/status/{task_id}/token_usage",
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@router.get("/task/{task_id}/testcases")
async def get_task_testcases(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Return the generated test case report for a specific audit task."""
    session = db.query(AuditSession).filter_by(task_id=task_id).first()
    _assert_session_ownership(session, current_user)

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            headers = _build_context_headers(current_user)
            response = await client.get(
                f"{AGENT_SERVICE_URL}/status/{task_id}/testcases",
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/telemetry")
async def get_agents_telemetry(
    current_user: User = Depends(get_current_user)
):
    """Fetch global agent telemetry metrics from Agent Service."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            headers = _build_context_headers(current_user)
            response = await client.get(
                f"{AGENT_SERVICE_URL}/agents/telemetry",
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/telemetry/stream")
async def stream_agents_telemetry(
    current_user: User = Depends(get_current_user)
):
    """Proxy global real-time event stream from Agent Service."""
    headers = _build_context_headers(current_user)
    
    async def event_generator():
        async with httpx.AsyncClient(timeout=None) as client:
            try:
                async with client.stream(
                    "GET",
                    f"{AGENT_SERVICE_URL}/agents/telemetry/stream",
                    headers=headers,
                    timeout=None
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        yield f"{line}\n"
            except Exception as e:
                # Log error or send error SSE event
                yield f"data: {{\"error\": \"Proxy stream error: {str(e)}\"}}\n\n"
                    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )


@router.post("/task/{task_id}/stop")
async def stop_audit_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Stop an ongoing audit task."""
    session = db.query(AuditSession).filter_by(task_id=task_id).first()
    _assert_session_ownership(session, current_user)

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            headers = _build_context_headers(current_user)
            response = await client.post(
                f"{AGENT_SERVICE_URL}/status/{task_id}/stop",
                headers=headers
            )
            response.raise_for_status()
            
            # Also update local gateway database session status to stopped
            if session:
                session.status = "stopped"
                db.commit()
                
            return response.json()
        except Exception as e:
            logger.exception(f"Error stopping task {task_id}")
            raise HTTPException(status_code=500, detail=str(e))


@router.post("/task/{task_id}/pause")
async def pause_audit_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Pause an ongoing audit task."""
    session = db.query(AuditSession).filter_by(task_id=task_id).first()
    _assert_session_ownership(session, current_user)

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            headers = _build_context_headers(current_user)
            response = await client.post(
                f"{AGENT_SERVICE_URL}/status/{task_id}/pause",
                headers=headers
            )
            response.raise_for_status()
            
            if session:
                session.status = "paused"
                db.commit()
                
            return response.json()
        except Exception as e:
            logger.exception(f"Error pausing task {task_id}")
            raise HTTPException(status_code=500, detail=str(e))


@router.post("/task/{task_id}/resume")
async def resume_audit_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Resume a paused audit task."""
    session = db.query(AuditSession).filter_by(task_id=task_id).first()
    _assert_session_ownership(session, current_user)

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            headers = _build_context_headers(current_user)
            response = await client.post(
                f"{AGENT_SERVICE_URL}/status/{task_id}/resume",
                headers=headers
            )
            response.raise_for_status()
            
            # The agent service returns the new status ("auditing" or "crawling")
            res_data = response.json()
            if session:
                session.status = res_data.get("status", "auditing")
                db.commit()
                
            return res_data
        except Exception as e:
            logger.exception(f"Error resuming task {task_id}")
            raise HTTPException(status_code=500, detail=str(e))


@router.delete("/task/{task_id}")
async def delete_audit_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an audit session and clean up downstream task progress."""
    session = db.query(AuditSession).filter_by(task_id=task_id).first()
    _assert_session_ownership(session, current_user)

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            headers = _build_context_headers(current_user)
            # Instruct downstream agent to delete progress row
            response = await client.delete(
                f"{AGENT_SERVICE_URL}/status/{task_id}",
                headers=headers
            )
            
            # Delete local database session (cascades to violations)
            if session:
                db.delete(session)
                db.commit()
                
            return {"status": "deleted", "task_id": task_id}
        except Exception as e:
            logger.exception(f"Error deleting task {task_id}")
            raise HTTPException(status_code=500, detail=str(e))


