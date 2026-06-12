import httpx
import logging
from typing import Optional
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from common.database.models import User, AuditSession
from common.schemas.audit import AuditRequest, AuditTask
from common.utils.correlation import get_correlation_headers
from common.config import get_service_url
from app.repository.proxy_repo import proxy_repo

logger = logging.getLogger(__name__)

AGENT_SERVICE_URL = get_service_url("AGENT_SERVICE_URL", "http://agent:8001", "http://localhost:8001")

class ProxyService:
    def _build_context_headers(self, current_user: User, project_id: Optional[str] = None) -> dict:
        headers = get_correlation_headers()
        headers["X-User-ID"] = str(current_user.id)
        headers["X-Organization-ID"] = str(current_user.organization_id)
        headers["X-User-Role"] = str(current_user.role)
        if project_id:
            headers["X-Project-ID"] = str(project_id)
        return headers

    def _assert_session_ownership(self, session: Optional[AuditSession], current_user: User) -> None:
        if session and session.organization_id != current_user.organization_id:
            raise HTTPException(
                status_code=403,
                detail="Access denied. Audit session belongs to another workspace."
            )

    async def start_audit(
        self,
        request: AuditRequest,
        project_id: Optional[str],
        current_user: User,
        db: Session
    ) -> AuditTask:
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
                headers = self._build_context_headers(current_user, project_id)

                if not project_id:
                    default_proj = proxy_repo.get_default_project_by_org(db, org_id)
                    if default_proj:
                        headers["X-Project-ID"] = str(default_proj.id)

                response = await client.post(
                    f"{AGENT_SERVICE_URL}/audit",
                    json=audit_data,
                    headers=headers
                )
                response.raise_for_status()
                return AuditTask(**response.json())
            except httpx.HTTPStatusError as hse:
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

    async def get_task_status(self, task_id: str, current_user: User, db: Session) -> AuditTask:
        session = proxy_repo.get_session_by_task_id(db, task_id)
        self._assert_session_ownership(session, current_user)

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                headers = self._build_context_headers(current_user)
                response = await client.get(
                    f"{AGENT_SERVICE_URL}/status/{task_id}",
                    headers=headers
                )
                response.raise_for_status()
                return AuditTask(**response.json())
            except Exception as e:
                logger.exception(f"Error fetching task status for task {task_id}")
                raise HTTPException(status_code=500, detail=str(e))

    async def get_task_token_usage(self, task_id: str, current_user: User, db: Session) -> dict:
        session = proxy_repo.get_session_by_task_id(db, task_id)
        self._assert_session_ownership(session, current_user)

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                headers = self._build_context_headers(current_user)
                response = await client.get(
                    f"{AGENT_SERVICE_URL}/status/{task_id}/token_usage",
                    headers=headers
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

    async def get_task_testcases(self, task_id: str, current_user: User, db: Session) -> dict:
        session = proxy_repo.get_session_by_task_id(db, task_id)
        self._assert_session_ownership(session, current_user)

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                headers = self._build_context_headers(current_user)
                response = await client.get(
                    f"{AGENT_SERVICE_URL}/status/{task_id}/testcases",
                    headers=headers
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

    async def get_agents_telemetry(self, current_user: User) -> dict:
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                headers = self._build_context_headers(current_user)
                response = await client.get(
                    f"{AGENT_SERVICE_URL}/agents/telemetry",
                    headers=headers
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

    def stream_agents_telemetry(self, current_user: User) -> StreamingResponse:
        headers = self._build_context_headers(current_user)

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
                    yield f"data: {{\"error\": \"Proxy stream error: {str(e)}\"}}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            }
        )

    async def stop_audit_task(self, task_id: str, current_user: User, db: Session) -> dict:
        session = proxy_repo.get_session_by_task_id(db, task_id)
        self._assert_session_ownership(session, current_user)

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                headers = self._build_context_headers(current_user)
                response = await client.post(
                    f"{AGENT_SERVICE_URL}/status/{task_id}/stop",
                    headers=headers
                )
                response.raise_for_status()

                if session:
                    proxy_repo.update_session_status(db, session, "stopped")

                return response.json()
            except Exception as e:
                logger.exception(f"Error stopping task {task_id}")
                raise HTTPException(status_code=500, detail=str(e))

    async def pause_audit_task(self, task_id: str, current_user: User, db: Session) -> dict:
        session = proxy_repo.get_session_by_task_id(db, task_id)
        self._assert_session_ownership(session, current_user)

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                headers = self._build_context_headers(current_user)
                response = await client.post(
                    f"{AGENT_SERVICE_URL}/status/{task_id}/pause",
                    headers=headers
                )
                response.raise_for_status()

                if session:
                    proxy_repo.update_session_status(db, session, "paused")

                return response.json()
            except Exception as e:
                logger.exception(f"Error pausing task {task_id}")
                raise HTTPException(status_code=500, detail=str(e))

    async def resume_audit_task(self, task_id: str, current_user: User, db: Session) -> dict:
        session = proxy_repo.get_session_by_task_id(db, task_id)
        self._assert_session_ownership(session, current_user)

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                headers = self._build_context_headers(current_user)
                response = await client.post(
                    f"{AGENT_SERVICE_URL}/status/{task_id}/resume",
                    headers=headers
                )
                response.raise_for_status()

                res_data = response.json()
                if session:
                    proxy_repo.update_session_status(db, session, res_data.get("status", "auditing"))

                return res_data
            except Exception as e:
                logger.exception(f"Error resuming task {task_id}")
                raise HTTPException(status_code=500, detail=str(e))

    async def delete_audit_task(self, task_id: str, current_user: User, db: Session) -> dict:
        session = proxy_repo.get_session_by_task_id(db, task_id)
        self._assert_session_ownership(session, current_user)

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                headers = self._build_context_headers(current_user)
                response = await client.delete(
                    f"{AGENT_SERVICE_URL}/status/{task_id}",
                    headers=headers
                )

                if session:
                    proxy_repo.delete_session(db, session)

                return {"status": "deleted", "task_id": task_id}
            except Exception as e:
                logger.exception(f"Error deleting task {task_id}")
                raise HTTPException(status_code=500, detail=str(e))

proxy_service = ProxyService()
