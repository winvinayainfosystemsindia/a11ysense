"""
Routes — API routing definitions.
"""
from fastapi import APIRouter, BackgroundTasks, Request, HTTPException
from fastapi.responses import Response, StreamingResponse

from app.schemas import AuditRequest, AuditTask
from app.services.orchestrator import audit_orchestrator
from app.services.telemetry import telemetry_service

router = APIRouter()


@router.get("/metrics")
def metrics() -> Response:
    """Prometheus metrics endpoint."""
    return telemetry_service.get_metrics_response()


@router.post("/audit", response_model=AuditTask)
async def start_audit(
    request: AuditRequest,
    fastapi_req: Request,
    background_tasks: BackgroundTasks
) -> AuditTask:
    """Start a new audit (background task)."""
    org_id = fastapi_req.headers.get("X-Organization-ID")
    proj_id = fastapi_req.headers.get("X-Project-ID")
    return await audit_orchestrator.start_audit(request, org_id, proj_id, background_tasks)


@router.get("/status/{task_id}", response_model=AuditTask)
async def get_status(task_id: str) -> AuditTask:
    """Poll current status (JSON)."""
    return await audit_orchestrator.get_status(task_id)


@router.get("/status/{task_id}/stream")
async def stream_task_status(task_id: str) -> StreamingResponse:
    """Real-time SSE progress stream."""
    return await audit_orchestrator.stream_task_status(task_id)


@router.get("/status/{task_id}/token_usage")
async def get_status_token_usage(task_id: str) -> dict:
    """LLM token consumption."""
    return await audit_orchestrator.get_status_token_usage(task_id)


@router.get("/status/{task_id}/testcases")
async def get_status_testcases(task_id: str) -> list:
    """Generated test case report."""
    return await audit_orchestrator.get_testcase_report(task_id)


@router.post("/status/{task_id}/stop")
async def stop_status(task_id: str) -> dict:
    """Stop a running audit task."""
    res = await audit_orchestrator.stop_audit(task_id)
    if not res:
        raise HTTPException(status_code=404, detail="Task not found")
    return res


@router.post("/status/{task_id}/pause")
async def pause_status(task_id: str) -> dict:
    """Pause a running audit task."""
    res = await audit_orchestrator.pause_audit(task_id)
    if not res:
        raise HTTPException(status_code=404, detail="Task not found")
    return res


@router.post("/status/{task_id}/resume")
async def resume_status(task_id: str) -> dict:
    """Resume a paused audit task."""
    res = await audit_orchestrator.resume_audit(task_id)
    if not res:
        raise HTTPException(status_code=404, detail="Task not found")
    return res


@router.delete("/status/{task_id}")
async def delete_status(task_id: str) -> dict:
    """Delete progress row."""
    return await audit_orchestrator.delete_audit(task_id)


@router.get("/agents/telemetry")
async def get_agents_telemetry() -> dict:
    """Fetch aggregated cluster-level agents telemetry statistics."""
    return await telemetry_service.get_agents_telemetry()


@router.get("/agents/telemetry/stream")
async def stream_agents_telemetry() -> StreamingResponse:
    """SSE stream of live audit progress telemetry events across the entire cluster."""
    return await telemetry_service.stream_agents_telemetry()
