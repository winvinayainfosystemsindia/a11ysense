"""
TelemetryService — Service for exposing Prometheus metrics and SSE telemetry progress.
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any

from starlette.responses import Response
from prometheus_client import Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import StreamingResponse

from app.repository.session_repo import audit_session_repo

logger = logging.getLogger(__name__)

# Custom OpenClaw Agent Cluster Metrics
GAUGE_ACTIVE_AUDITS = Gauge("openclaw_active_audits", "Count of active audit sessions")
GAUGE_TOTAL_AUDITS = Gauge("openclaw_total_audits", "Total count of audit sessions")
GAUGE_COMPLETED_AUDITS = Gauge("openclaw_completed_audits", "Count of completed audit sessions")
GAUGE_FAILED_AUDITS = Gauge("openclaw_failed_audits", "Count of failed audit sessions")
GAUGE_TOTAL_TOKENS = Gauge("openclaw_llm_tokens_total", "Total LLM tokens consumed across sessions")


class TelemetryService:

    def update_db_metrics(self) -> None:
        """Fetch database-level totals and set the corresponding Prometheus gauges."""
        try:
            data = audit_session_repo.get_telemetry_data()
            GAUGE_ACTIVE_AUDITS.set(data["active_count"])
            GAUGE_TOTAL_AUDITS.set(data["total_count"])
            GAUGE_COMPLETED_AUDITS.set(data["completed_count"])
            GAUGE_FAILED_AUDITS.set(data["failed_count"])
            GAUGE_TOTAL_TOKENS.set(data["total_tokens"])
        except Exception as e:
            logger.error(f"Failed to update prometheus db metrics: {e}")

    def get_metrics_response(self) -> Response:
        """Endpoint backend function to return formatted Prometheus scraping output."""
        self.update_db_metrics()
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

    async def get_agents_telemetry(self) -> Dict[str, Any]:
        """Aggregate telemetry details for single-endpoint JSON reads."""
        try:
            data = audit_session_repo.get_telemetry_data()
            return {
                "active_agents_count": data["active_count"],
                "active_tasks": data["active_tasks"],
                "total_tasks_run": data["total_count"],
                "completed_tasks_run": data["completed_count"],
                "failed_tasks_run": data["failed_count"],
                "total_violations_found": data["total_violations_found"],
                "tokens": {
                    "input_tokens": data["total_input_tokens"],
                    "output_tokens": data["total_output_tokens"],
                    "total_tokens": data["total_tokens"]
                }
            }
        except Exception as e:
            logger.error(f"Failed to fetch agents telemetry: {str(e)}")
            return {
                "active_agents_count": 0,
                "active_tasks": [],
                "total_tasks_run": 0,
                "completed_tasks_run": 0,
                "failed_tasks_run": 0,
                "total_violations_found": 0,
                "tokens": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
            }

    async def stream_agents_telemetry(self) -> StreamingResponse:
        """SSE stream of live audit progress telemetry events across the entire cluster."""
        from common.database.connection import get_session_local
        from common.database.models import AuditProgress
        
        async def event_generator():
            last_emitted_states = {} # task_id -> (status, pages_completed)
            
            while True:
                db = get_session_local()()
                try:
                    # Query tasks updated in the last hour
                    rows = db.query(AuditProgress).order_by(AuditProgress.updated_at.desc()).limit(15).all()
                    for row in rows:
                        task_id = row.task_id
                        status = row.status
                        pages_completed = row.pages_completed or 0
                        pages_total = row.pages_total or 0
                        
                        # Only emit if state changed
                        prev = last_emitted_states.get(task_id)
                        if not prev or prev[0] != status or prev[1] != pages_completed:
                            last_emitted_states[task_id] = (status, pages_completed)
                            
                            # Format message
                            time_str = datetime.utcnow().strftime("%H:%M:%S")
                            url_clean = row.url.replace("http://", "").replace("https://", "").split("/")[0]
                            
                            agent_name = "System"
                            msg_type = "info"
                            message = ""
                            
                            if status == "crawling":
                                agent_name = "Agent Spectre"
                                message = f"Crawling pages on {url_clean}..."
                                msg_type = "info"
                            elif status == "auditing":
                                agent_name = "Agent X-Ray"
                                message = f"Auditing {url_clean} — scanned {pages_completed}/{pages_total} pages."
                                msg_type = "info"
                            elif status == "completed":
                                agent_name = "System"
                                message = f"Audit completed for {url_clean} successfully."
                                msg_type = "success"
                            elif status == "failed":
                                agent_name = "System"
                                message = f"Audit failed for {url_clean}: {row.error or 'Unknown error'}"
                                msg_type = "error"
                            else:
                                message = f"Task {task_id} state transition to {status}."
                                msg_type = "info"

                            payload = json.dumps({
                                "time": time_str,
                                "agent": agent_name,
                                "message": message,
                                "type": msg_type,
                                "task_id": task_id,
                                "status": status,
                                "pages_completed": pages_completed,
                                "pages_total": pages_total
                            })
                            yield f"data: {payload}\n\n"
                except Exception as e:
                    logger.error(f"Telemetry stream error: {str(e)}")
                finally:
                    db.close()
                    
                await asyncio.sleep(2.0)

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            }
        )


telemetry_service = TelemetryService()
