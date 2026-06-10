"""
A11ySense AI — Agent Service

Orchestrates multi-agent accessibility audits. All task state is persisted
to PostgreSQL via AuditProgressRepo — no in-memory ACTIVE_TASKS dict.

Endpoints:
  POST /audit                        — start a new audit (background task)
  GET  /status/{task_id}             — poll current status (JSON)
  GET  /status/{task_id}/stream      — real-time SSE progress stream
  GET  /status/{task_id}/token_usage — LLM token consumption
  GET  /status/{task_id}/testcases   — generated test case report
"""
import asyncio
import sys
import os
import uuid
import json
import threading
from datetime import datetime
from typing import Optional
import logging
from common.utils.event_bus import publish_event, read_events, get_redis_client
from common.constants import parse_wcag_tags

# Windows event loop policy patch
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from common.config import setup_environment, get_storage_path, get_cors_origins, get_audit_storage_path
setup_environment()

logger = logging.getLogger(__name__)

from fastapi import FastAPI, BackgroundTasks, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from app.schemas import AuditRequest, AuditTask
from app.services.audit_service import audit_service
from app.services.agent_logic import agent_intelligence

# Repository — single source of truth for live task progress
from app.repository.audit_repo import audit_progress_repo

# Database — AuditSession (summary) + org/project resolution
from common.database.connection import get_session_local
from common.database.models import AuditSession, Organization, Project, ViolationRecord, AuditProgress

app = FastAPI(title="OpenClaw Agent Service")

from common.exceptions.handler import setup_global_exception_handler
setup_global_exception_handler(app, "agent-service")

# ── Telemetry & Metrics Monitoring ─────────────────────────────────────────

from starlette.responses import Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, Gauge
from prometheus_fastapi_instrumentator import Instrumentator

# Custom OpenClaw Agent Cluster Metrics
GAUGE_ACTIVE_AUDITS = Gauge("openclaw_active_audits", "Count of active audit sessions")
GAUGE_TOTAL_AUDITS = Gauge("openclaw_total_audits", "Total count of audit sessions")
GAUGE_COMPLETED_AUDITS = Gauge("openclaw_completed_audits", "Count of completed audit sessions")
GAUGE_FAILED_AUDITS = Gauge("openclaw_failed_audits", "Count of failed audit sessions")
GAUGE_TOTAL_TOKENS = Gauge("openclaw_llm_tokens_total", "Total LLM tokens consumed across sessions")

def update_db_metrics():
    db = get_session_local()()
    try:
        active = db.query(AuditSession).filter(AuditSession.status.in_(["crawling", "auditing"])).count()
        total = db.query(AuditSession).count()
        completed = db.query(AuditSession).filter(AuditSession.status == "completed").count()
        failed = db.query(AuditSession).filter(AuditSession.status == "failed").count()
        
        # Calculate tokens
        total_tokens = 0
        sessions = db.query(AuditSession).filter(AuditSession.summary.isnot(None)).all()
        for s in sessions:
            summary = s.summary or {}
            tok = summary.get("token_usage", {})
            total_tokens += tok.get("tokens_total", 0) or (tok.get("tokens_sent", 0) + tok.get("tokens_received", 0))
            
        GAUGE_ACTIVE_AUDITS.set(active)
        GAUGE_TOTAL_AUDITS.set(total)
        GAUGE_COMPLETED_AUDITS.set(completed)
        GAUGE_FAILED_AUDITS.set(failed)
        GAUGE_TOTAL_TOKENS.set(total_tokens)
    except Exception as e:
        logger.error(f"Failed to update prometheus db metrics: {e}")
    finally:
        db.close()

# Instrument the app middleware (latency, status codes, etc.)
Instrumentator().instrument(app)

# Custom metrics endpoint running DB updates before scrapers consume the metrics
@app.get("/metrics")
def metrics():
    update_db_metrics()
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from common.config import get_service_url
REPORTING_SERVICE_URL = get_service_url("REPORTING_SERVICE_URL", "http://reporting:8002", "http://localhost:8002")

from app.agents.manager import ManagerAgent
manager_agent = ManagerAgent()


# ── Helpers ────────────────────────────────────────────────────────────────

async def fetch_and_format_token_usage(task_id: str) -> dict:
    """Fetch token usage from the LLM service for the given task."""
    progress = audit_progress_repo.get(task_id)
    url = progress.url if progress else ""
    created_at_dt = progress.created_at if progress else None
    audited_at = created_at_dt.isoformat() if created_at_dt else datetime.utcnow().isoformat()

    llm_service_url = get_service_url("LLM_SERVICE_URL", "http://llm:8005", "http://localhost:8005")

    provider = "mock"
    tokens_sent = 0
    tokens_received = 0
    tokens_total = 0
    llm_calls = 0
    breakdown = {}

    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{llm_service_url}/session/{task_id}", timeout=1.5)
            if response.status_code == 200:
                data = response.json()
                provider = data.get("provider") or provider
                tokens_sent = data.get("total_input_tokens", 0)
                tokens_received = data.get("total_output_tokens", 0)
                tokens_total = data.get("total_tokens", 0)
                llm_calls = data.get("total_requests", 0)
                breakdown = data.get("breakdown", {})
    except Exception as e:
        logger.debug(f"LLM token summary unavailable for task {task_id}: {type(e).__name__}: {e}")

    return {
        "task_id": task_id,
        "url": url,
        "audited_at": audited_at,
        "provider": provider,
        "tokens_sent": tokens_sent,
        "tokens_received": tokens_received,
        "tokens_total": tokens_total,
        "llm_calls": llm_calls,
        "breakdown": breakdown
    }


async def run_in_memory_audit_flow(
    task_id: str,
    request: AuditRequest,
    org_id: Optional[str] = None,
    proj_id: Optional[str] = None
):
    """
    Bypasses Redis and runs the crawl and audit sequence in-memory using BackgroundTasks.
    """
    import traceback
    
    def write_debug(msg: str):
        try:
            log_path = os.path.join(get_storage_path(), "in_memory_debug.log")
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.utcnow().isoformat()}] [TASK {task_id}] {msg}\n")
        except Exception as e:
            print(f"Failed to write debug log: {str(e)}")

    write_debug(f"ENTERED run_in_memory_audit_flow for URL: {request.url}, depth: {request.depth}")
    
    discovered_urls = [str(request.url)]
    sitemaps_found = []
    crawl_error = None
    
    # 1. Run Crawler if depth > 1
    if request.depth > 1:
        from common.config import get_service_url
        crawler_service_url = get_service_url("CRAWLER_SERVICE_URL", "http://crawler:8003", "http://localhost:8003")
        try:
            write_debug(f"Calling crawler service at {crawler_service_url}/crawl...")
            import httpx
            async with httpx.AsyncClient() as client:
                payload = {
                    "url": str(request.url),
                    "depth": request.depth,
                    "max_pages": 30,
                    "respect_robots_txt": True
                }
                response = await client.post(f"{crawler_service_url}/crawl", json=payload, timeout=60.0)
                write_debug(f"Crawler response status: {response.status_code}")
                response.raise_for_status()
                crawl_data = response.json()
                discovered_urls = crawl_data.get("pages_discovered", [str(request.url)])
                sitemaps_found = crawl_data.get("sitemaps_found", [])
                write_debug(f"Crawler completed. Discovered {len(discovered_urls)} URLs: {discovered_urls}")
        except Exception as e:
            err_trace = traceback.format_exc()
            write_debug(f"Crawl failed: {str(e)}\nTraceback:\n{err_trace}")
            crawl_error = str(e)
    else:
        write_debug("Crawl depth is 1. Skipping crawler call.")

    # 2. Update DB states
    try:
        write_debug("Updating DB states to auditing...")
        audit_progress_repo.set_status(task_id, "auditing")
        audit_progress_repo.set_pages(
            task_id,
            pages_found=len(discovered_urls),
            pages_total=len(discovered_urls),
            pages_discovered=discovered_urls,
        )
        write_debug("DB states updated to auditing successfully.")
    except Exception as e:
        err_trace = traceback.format_exc()
        write_debug(f"Failed to update progress status to auditing: {str(e)}\nTrace:\n{err_trace}")

    # 3. If there was a crawl error AND no pages were discovered, fail immediately
    if crawl_error and request.depth > 1 and len(discovered_urls) <= 1:
        write_debug("Crawl discovery failed with no pages found, marking task as failed in DB...")
        audit_progress_repo.mark_failed(task_id, f"Crawl discovery failed downstream: {crawl_error}", {})
        db_fail = get_session_local()()
        try:
            session_rec = db_fail.query(AuditSession).filter_by(task_id=task_id).first()
            if session_rec:
                session_rec.status = "failed"
                session_rec.summary = {
                    "error": f"Crawl discovery failed downstream: {crawl_error}",
                    "accessibility_score": 0.0,
                    "total_violations": 0,
                    "passes_count": 0,
                    "token_usage": {}
                }
                db_fail.commit()
            write_debug("Recorded fail state in DB successfully.")
        except Exception as fail_db_err:
            write_debug(f"Failed to record fail state in DB: {fail_db_err}")
            db_fail.rollback()
        finally:
            db_fail.close()
        return
    elif crawl_error:
        # Non-fatal crawl warning (e.g. sitemap parse error) — proceed with discovered pages
        write_debug(f"Non-fatal crawl warning: {crawl_error}. Proceeding with {len(discovered_urls)} discovered URL(s).")

    # 4. Orchestrate audit
    try:
        write_debug(f"Orchestrating multi-agent audit scanning for URLs: {discovered_urls}")
        await orchestrate_agent_audit(
            task_id=task_id,
            request=request,
            discovered_urls=discovered_urls,
            sitemaps_found=sitemaps_found,
            org_id=org_id,
            proj_id=proj_id
        )
        write_debug("Orchestrated audit completed successfully.")
    except Exception as run_err:
        err_trace = traceback.format_exc()
        write_debug(f"Orchestrated audit failed: {str(run_err)}\nTrace:\n{err_trace}")
        audit_progress_repo.mark_failed(task_id, str(run_err), {})
        db_fail = get_session_local()()
        try:
            session_rec = db_fail.query(AuditSession).filter_by(task_id=task_id).first()
            if session_rec:
                session_rec.status = "failed"
                session_rec.summary = {
                    "error": str(run_err),
                    "accessibility_score": 0.0,
                    "total_violations": 0,
                    "passes_count": 0,
                    "token_usage": {}
                }
                db_fail.commit()
            write_debug("Recorded audit failure in DB successfully.")
        except Exception as fail_db_err:
            write_debug(f"Failed to record audit failure in DB: {fail_db_err}")
            db_fail.rollback()
        finally:
            db_fail.close()


# ── Audit endpoint ─────────────────────────────────────────────────────────

@app.post("/audit", response_model=AuditTask)
async def start_audit(request: AuditRequest, fastapi_req: Request, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())

    # Retrieve multi-tenant scope headers propagated from Gateway
    org_id = fastapi_req.headers.get("X-Organization-ID")
    proj_id = fastapi_req.headers.get("X-Project-ID")

    # 1. Write initial AuditProgress row to PostgreSQL
    progress_row = audit_progress_repo.create(task_id, str(request.url))

    # 2. Bootstrap AuditSession record (for org-level reporting)
    db = get_session_local()()
    try:
        resolved_org_id = None
        if org_id:
            resolved_org_id = uuid.UUID(org_id)
        else:
            first_org = db.query(Organization).first()
            if first_org:
                resolved_org_id = first_org.id

        resolved_proj_id = None
        if proj_id:
            resolved_proj_id = uuid.UUID(proj_id)
        else:
            if resolved_org_id:
                default_proj = db.query(Project).filter_by(name="Default Project", organization_id=resolved_org_id).first()
                if default_proj:
                    resolved_proj_id = default_proj.id

        session_record = AuditSession(
            task_id=task_id,
            url=str(request.url),
            status="crawling",
            organization_id=resolved_org_id,
            project_id=resolved_proj_id,
            timestamp=datetime.utcnow()
        )
        db.add(session_record)
        db.commit()
    except Exception as db_err:
        print(f"Failed to bootstrap audit session in PostgreSQL: {str(db_err)}")
        db.rollback()
    finally:
        db.close()

    # Immediately set progress status to crawling
    audit_progress_repo.set_status(task_id, "crawling")

    # Publish to Redis Stream "audit:tasks"
    task_payload = {
        "task_id": task_id,
        "url": str(request.url),
        "depth": request.depth,
        "audit_type": request.audit_type,
        "org_id": org_id,
        "proj_id": proj_id
    }
    
    if get_redis_client() is not None:
        publish_event("audit:tasks", task_payload)
    else:
        logger.info(f"Redis is offline. Triggering audit for task {task_id} in-memory via BackgroundTasks.")
        background_tasks.add_task(
            run_in_memory_audit_flow,
            task_id=task_id,
            request=request,
            org_id=org_id,
            proj_id=proj_id
        )

    # Return initial status directly (crawling takes over asynchronously)
    return audit_progress_repo.as_audit_task(task_id) or progress_row


# ── Status endpoints ───────────────────────────────────────────────────────

@app.get("/status/{task_id}", response_model=AuditTask)
async def get_status(task_id: str):
    """
    Returns the current audit status.
    Reads from AuditProgress (PostgreSQL) — survives restarts.
    Falls back to AuditSession summary if progress row is missing.
    """
    # 1. Primary: AuditProgress table (live progress)
    audit_task = audit_progress_repo.as_audit_task(task_id)
    if audit_task:
        if audit_task.status in ["completed", "failed", "stopped"]:
            db = get_session_local()()
            try:
                session_rec = db.query(AuditSession).filter_by(task_id=task_id).first()
                if session_rec:
                    audit_task.summary = session_rec.summary
            except Exception as e:
                logger.error(f"Failed to enrich completed audit task summary: {e}")
            finally:
                db.close()
        else:
            # Enrich token usage if still running
            try:
                audit_task.token_usage = await fetch_and_format_token_usage(task_id)
            except Exception:
                pass
        return audit_task

    # 2. Fallback: AuditSession table (summary after completion)
    db = get_session_local()()
    try:
        session_rec = db.query(AuditSession).filter_by(task_id=task_id).first()
        if session_rec:
            summary = session_rec.summary or {}
            passes_count = summary.get("passes_count", 0)
            total_violations = summary.get("total_violations", 0)
            pages_total = passes_count + total_violations
            report_url = f"http://localhost:8002/report/{task_id}" if session_rec.status == "completed" else None

            return AuditTask(
                task_id=task_id,
                status=session_rec.status,
                url=session_rec.url,
                created_at=session_rec.timestamp,
                report_url=report_url,
                pages_found=pages_total,
                pages_completed=pages_total,
                pages_total=pages_total,
                pages_scanned=[session_rec.url] if session_rec.status == "completed" else [],
                pages_discovered=[session_rec.url] if session_rec.status == "completed" else [],
                error=summary.get("error"),
                token_usage=summary.get("token_usage"),
                summary=summary
            )
    except Exception as e:
        print(f"Failed to query status from PostgreSQL: {str(e)}")
    finally:
        db.close()

    return AuditTask(task_id=task_id, status="not_found")


@app.get("/status/{task_id}/stream")
async def stream_task_status(task_id: str):
    """
    Server-Sent Events (SSE) stream for real-time audit progress.
    The client receives a JSON event every 1.5 seconds until the audit
    reaches a terminal state (completed / failed / not_found).

    Usage (JavaScript):
        const es = new EventSource('/status/<task_id>/stream');
        es.onmessage = e => console.log(JSON.parse(e.data));
    """
    async def event_generator():
        while True:
            row = audit_progress_repo.get(task_id)
            if row is None:
                # Task not found — send one error event and close
                payload = json.dumps({"task_id": task_id, "status": "not_found"})
                yield f"data: {payload}\n\n"
                break

            task_data = row
            payload = json.dumps({
                "task_id": task_data.task_id,
                "status": task_data.status,
                "url": str(task_data.url),
                "pages_found": task_data.pages_found,
                "pages_completed": task_data.pages_completed,
                "pages_total": task_data.pages_total,
                "pages_scanned": task_data.pages_scanned,
                "pages_discovered": task_data.pages_discovered,
                "report_url": task_data.report_url,
                "error": task_data.error,
            })
            yield f"data: {payload}\n\n"

            # Stop streaming once we hit a terminal state
            if task_data.status in ["completed", "failed"]:
                break

            await asyncio.sleep(1.5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",   # Disable nginx buffering for SSE
        }
    )


@app.get("/status/{task_id}/token_usage")
async def get_status_token_usage(task_id: str):
    """Return LLM token usage. Reads from AuditProgress if completed, else fetches live."""
    row = audit_progress_repo.get(task_id)
    if row and row.token_usage:
        return row.token_usage
    return await fetch_and_format_token_usage(task_id)


@app.get("/status/{task_id}/testcases")
async def get_status_testcases(task_id: str):
    """Return the generated test case JSON report for a completed audit."""
    reports_dir = get_audit_storage_path(task_id)
    json_path = os.path.join(reports_dir, f"testcase_report_{task_id}.json")
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


@app.post("/status/{task_id}/stop")
async def stop_status(task_id: str):
    progress = audit_progress_repo.get(task_id)
    if not progress:
        raise HTTPException(status_code=404, detail="Task not found")
    audit_progress_repo.set_status(task_id, "stopped")
    
    # Also update AuditSession status
    db = get_session_local()()
    try:
        session_rec = db.query(AuditSession).filter_by(task_id=task_id).first()
        if session_rec:
            session_rec.status = "stopped"
            db.commit()
    except Exception as e:
        logger.error(f"Failed to set status to stopped in DB: {e}")
        db.rollback()
    finally:
        db.close()
        
    return {"status": "stopped", "task_id": task_id}


@app.post("/status/{task_id}/pause")
async def pause_status(task_id: str):
    progress = audit_progress_repo.get(task_id)
    if not progress:
        raise HTTPException(status_code=404, detail="Task not found")
    audit_progress_repo.set_status(task_id, "paused")
    
    db = get_session_local()()
    try:
        session_rec = db.query(AuditSession).filter_by(task_id=task_id).first()
        if session_rec:
            session_rec.status = "paused"
            db.commit()
    except Exception as e:
        logger.error(f"Failed to set status to paused in DB: {e}")
        db.rollback()
    finally:
        db.close()
        
    return {"status": "paused", "task_id": task_id}


@app.post("/status/{task_id}/resume")
async def resume_status(task_id: str):
    progress = audit_progress_repo.get(task_id)
    if not progress:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Check what state we should resume to: if we have scanned pages, resume to auditing, else crawling
    new_status = "auditing" if progress.pages_found > 0 else "crawling"
    audit_progress_repo.set_status(task_id, new_status)
    
    db = get_session_local()()
    try:
        session_rec = db.query(AuditSession).filter_by(task_id=task_id).first()
        if session_rec:
            session_rec.status = new_status
            db.commit()
    except Exception as e:
        logger.error(f"Failed to set status to resumed in DB: {e}")
        db.rollback()
    finally:
        db.close()
        
    return {"status": new_status, "task_id": task_id}


@app.delete("/status/{task_id}")
async def delete_status(task_id: str):
    # Delete progress row
    audit_progress_repo.delete(task_id)
    return {"status": "deleted", "task_id": task_id}


# ── Orchestration ──────────────────────────────────────────────────────────

async def orchestrate_agent_audit(
    task_id: str,
    request: AuditRequest,
    discovered_urls: list[str],
    sitemaps_found: list[str],
    org_id: Optional[str] = None,
    proj_id: Optional[str] = None
):
    import httpx
    from common.utils.correlation import get_correlation_headers
    headers = get_correlation_headers()

    # Mark AuditSession as auditing
    db = get_session_local()()
    try:
        session_rec = db.query(AuditSession).filter_by(task_id=task_id).first()
        if session_rec:
            session_rec.status = "auditing"
            db.commit()
    except Exception as pg_err:
        print(f"Failed to update session status to auditing in DB: {str(pg_err)}")
        db.rollback()
    finally:
        db.close()

    try:
        # Execute the Multi-Agent Audit using pre-discovered URLs from Redis crawl results
        refined_result = await manager_agent.run_audit(
            request,
            task_id=task_id,
            pre_discovered_urls=discovered_urls,
            pre_sitemaps_found=sitemaps_found
        )

        # Route raw results to Analyzer Service
        ANALYZER_SERVICE_URL = get_service_url("ANALYZER_SERVICE_URL", "http://analyzer:8004", "http://localhost:8004")
        try:
            print(f"Routing raw compliance results to central Analyzer Service: {ANALYZER_SERVICE_URL}")
            async with httpx.AsyncClient() as client:
                analyzer_payload = refined_result.model_dump(mode='json')
                analyzer_response = await client.post(
                    f"{ANALYZER_SERVICE_URL}/analyze",
                    json=analyzer_payload,
                    headers=headers,
                    timeout=30.0
                )
                analyzer_response.raise_for_status()
                analyzed_data = analyzer_response.json()

                from app.schemas import Violation
                refined_result.violations = [Violation(**v) for v in analyzed_data.get("violations", [])]
                refined_result.metadata["accessibility_score"] = analyzed_data.get("accessibility_score", 100.0)
                refined_result.metadata["score_breakdown"] = analyzed_data.get("score_breakdown", {})
                refined_result.metadata["trend"] = analyzed_data.get("trend", {})
                print(f"Analyzer Service resolved (Score={refined_result.metadata['accessibility_score']})")
        except Exception as e:
            print(f"Analyzer Service unavailable, falling back: {str(e)}")

        # Compile final token usage report
        token_usage = await fetch_and_format_token_usage(task_id)
        refined_result.metadata["token_usage"] = token_usage

        report_url = f"http://localhost:8002/report/{task_id}"

        # Compile and save test case reports (CSV / JSON / MD)
        try:
            await compile_and_save_testcase_report(task_id, refined_result, org_id=org_id, proj_id=proj_id)
        except Exception as tc_err:
            print(f"Failed to generate testcase report: {str(tc_err)}")



        # Check if stopped early by user
        final_progress = audit_progress_repo.get(task_id)
        is_stopped = final_progress and final_progress.status == "stopped"


        # Publish the finalized audit result onto stream "audit:analyzed" (only if Redis is online)
        if get_redis_client() is not None:
            try:
                publish_event("audit:analyzed", {
                    "task_id": task_id,
                    "result": refined_result.model_dump(mode='json'),
                    "report_url": report_url
                })
            except Exception as pub_err:
                logger.warning(f"Failed to publish audit:analyzed event: {pub_err}")

        # Bypassing Redis fallback: directly trigger Allure report generation over HTTP if Redis is unavailable
        if get_redis_client() is None:
            try:
                print(f"Redis is down. Directly POSTing report payload to Reporting Service: {REPORTING_SERVICE_URL}")
                async with httpx.AsyncClient() as client:
                    reporting_response = await client.post(
                        f"{REPORTING_SERVICE_URL}/generate",
                        params={"task_id": task_id},
                        json=refined_result.model_dump(mode='json'),
                        headers=headers,
                        timeout=30.0
                    )
                    reporting_response.raise_for_status()
                    print(f"Reporting Service successfully compiled Allure report for task {task_id}")
            except Exception as report_err:
                print(f"Failed to compile Allure report over direct HTTP fallback: {str(report_err)}")

        # Deduct credits based on consumption rates:
        # Crawl discovery: 1 credit per discovered page
        # LLM Reasoning: 5 credits per successfully scanned page
        pages_crawled = len(discovered_urls)
        pages_scanned = len(refined_result.metadata.get("summary", {}).get("pages_details", {}))
        if pages_scanned == 0:
            pages_scanned = pages_crawled
        
        credits_spent = pages_crawled + (5 * pages_scanned)
        
        if org_id:
            from common.billing.billing_manager import billing_manager
            db_billing = get_session_local()()
            try:
                billing_manager.deduct_credits(
                    db=db_billing,
                    org_id=uuid.UUID(org_id),
                    credits_spent=credits_spent,
                    task_id=task_id,
                    description=f"Automated audit execution on {request.url} ({pages_crawled} crawled, {pages_scanned} scanned)"
                )
            except Exception as billing_err:
                print(f"Failed to deduct billing credits: {billing_err}")
            finally:
                db_billing.close()

        # Persist full AuditSession summary + violations
        total_violations = len(refined_result.violations or [])
        violations_by_impact = {"critical": 0, "serious": 0, "moderate": 0, "minor": 0}
        for v in (refined_result.violations or []):
            impact = (v.impact or "moderate").lower()
            violations_by_impact[impact] = violations_by_impact.get(impact, 0) + 1

        summary_data = {
            "accessibility_score": refined_result.metadata.get("accessibility_score", 100.0),
            "total_violations": total_violations,
            "violations_by_impact": violations_by_impact,
            "passes_count": len(refined_result.passes or []) if refined_result.passes else 0,
            "token_usage": token_usage
        }

        db = get_session_local()()
        try:
            session_rec = db.query(AuditSession).filter_by(task_id=task_id).first()
            if session_rec:
                session_rec.status = "stopped" if is_stopped else "completed"
                session_rec.summary = summary_data
                db.query(ViolationRecord).filter_by(audit_session_id=session_rec.id).delete()
                for v in (refined_result.violations or []):
                    violation_rec = ViolationRecord(
                        audit_session_id=session_rec.id,
                        rule_id=v.id,
                        impact=v.impact,
                        description=v.description,
                        help=v.help,
                        help_url=getattr(v, 'helpUrl', getattr(v, 'help_url', None)),
                        nodes=v.nodes,
                        metadata_json=v.metadata
                    )
                    db.add(violation_rec)
                db.commit()
                print(f"Task {task_id} successfully persisted in PostgreSQL.")
        except Exception as pg_commit_err:
            print(f"Failed to commit complete audit result to PostgreSQL: {str(pg_commit_err)}")
            db.rollback()
        finally:
            db.close()

        # Mark progress as completed or stopped in PostgreSQL after summary is fully persisted
        if is_stopped:
            audit_progress_repo.set_status(task_id, "stopped")
        else:
            audit_progress_repo.mark_completed(task_id, token_usage, report_url)

        print(f"Task {task_id} completed successfully.")

    except Exception as e:
        print(f"Error in task {task_id}: {str(e)}")

        # Fetch and store token usage even on failure
        try:
            token_usage = await fetch_and_format_token_usage(task_id)
        except Exception:
            token_usage = {}



        # Mark progress as failed in PostgreSQL
        audit_progress_repo.mark_failed(task_id, str(e), token_usage)

        # Push to Redis DLQ only when Redis is available
        if get_redis_client() is not None:
            try:
                import redis
                redis_host = os.getenv("REDIS_HOST", "localhost")
                r_client = redis.Redis(host=redis_host, port=6379, db=0, socket_timeout=2.0)
                dlq_payload = {
                    "task_id": task_id,
                    "url": str(request.url),
                    "correlation_id": headers.get("X-Correlation-ID"),
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
                r_client.rpush("audit:dlq", json.dumps(dlq_payload))
                print(f"Task {task_id} failure pushed to Redis DLQ 'audit:dlq'.")
            except Exception as dlq_err:
                print(f"Failed to push task failure to Redis DLQ: {str(dlq_err)}")
        else:
            logger.warning(f"Redis unavailable — skipping DLQ push for failed task {task_id}.")

        # Update AuditSession status to failed
        db = get_session_local()()
        try:
            session_rec = db.query(AuditSession).filter_by(task_id=task_id).first()
            if session_rec:
                session_rec.status = "failed"
                session_rec.summary = {
                    "error": str(e),
                    "accessibility_score": 0.0,
                    "total_violations": 0,
                    "passes_count": 0,
                    "token_usage": token_usage
                }
                db.commit()
        except Exception as pg_fail_err:
            print(f"Failed to update failed status in PostgreSQL: {str(pg_fail_err)}")
            db.rollback()
        finally:
            db.close()


# ── Test case report compilation ───────────────────────────────────────────

def generate_tc_custom_id(url: str, page_title: str, counter: int) -> str:
    from urllib.parse import urlparse
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.split(':')[0]
        if domain.startswith("www."):
            domain = domain[4:]
        domain_parts = domain.split('.')
        if domain_parts:
            website = domain_parts[0]
            if website.lower() in ["localhost", "127", "10", "192", "172"]:
                website = "Website"
            else:
                website = website.capitalize()
        else:
            website = "Website"
    except Exception:
        website = "Website"

    title = (page_title or "Page").strip()
    title = " ".join(title.split())
    if len(title) > 30:
        title = title[:27] + "..."

    counter_str = f"{counter:03d}"
    return f"TC-{website}-{title} -{counter_str}"




def resolve_passed_metadata(p_id: str, tags: list, p_desc: str, p_help: str, p_metadata: dict = None) -> dict:
    # If the check contains inline metadata from custom skills, use it directly
    if p_metadata:
        return {
            "criteria": p_metadata.get("wcag_criteria", "N/A"),
            "level": p_metadata.get("wcag_level", "N/A"),
            "severity": p_metadata.get("severity", "Serious"),
            "expected_result": p_metadata.get("expected_result", "N/A"),
            "actual_result": p_metadata.get("actual_result", "N/A"),
            "steps_to_reproduce": p_metadata.get("steps_to_reproduce", "N/A"),
            "remediation": p_metadata.get("remediation", "N/A"),
            "business_impact": p_metadata.get("business_impact", "N/A")
        }

    # Otherwise, resolve dynamically using parse_wcag_tags
    criteria, level = parse_wcag_tags(tags)
    
    # Severity defaults to Serious for axe-core passes if not specified
    severity = "Serious"

    expected = f"The element should comply with accessibility requirements for rule '{p_id}': {p_desc or p_help}."
    actual = f"Verification passed: Element complies with accessibility requirements for rule '{p_id}'."
    if p_desc:
        actual += f" {p_desc}"
        
    steps = (
        f"1. Open the webpage in a browser.\n"
        f"2. Locate elements matching rule '{p_id}'.\n"
        f"3. Verify compliance with the rule: {p_desc or p_help}."
    )
    remediation = f"No remediation required. Rule '{p_id}' complies with accessibility requirements."
    business_impact = f"Ensures optimal user experience and prevents accessibility barriers related to: {p_help}."

    return {
        "criteria": criteria,
        "level": level,
        "severity": severity,
        "expected_result": expected,
        "actual_result": actual,
        "steps_to_reproduce": steps,
        "remediation": remediation,
        "business_impact": business_impact
    }

async def compile_and_save_testcase_report(task_id: str, result, org_id: str = None, proj_id: str = None) -> list:
    testcases = []
    counter = 1

    # ── PASSED test cases ─────────────────────────────────────────────────────
    if result.passes:
        for p in result.passes:
            p_id = p.get('id', 'Unknown') if isinstance(p, dict) else getattr(p, 'id', 'Unknown')
            p_help = p.get('help', p_id) if isinstance(p, dict) else getattr(p, 'help', p_id)
            p_desc = p.get('description', '') if isinstance(p, dict) else getattr(p, 'description', '')
            p_tags = p.get('tags', []) if isinstance(p, dict) else getattr(p, 'tags', [])
            p_help_url = p.get('helpUrl', p.get('help_url', '')) if isinstance(p, dict) else getattr(p, 'helpUrl', getattr(p, 'help_url', ''))
            
            p_metadata = p.get('metadata') if isinstance(p, dict) else getattr(p, 'metadata', None)
            meta = resolve_passed_metadata(p_id, p_tags, p_desc, p_help, p_metadata)
            
            page_title = result.metadata.get("page_title", "Page")
            custom_id = generate_tc_custom_id(result.url, page_title, counter)
            testcases.append({
                "testcase_id": custom_id,
                "defect_id": "N/A",
                "rule_id": p_id,
                "testcase_name": p_help,
                "description": p_desc,
                "criteria": meta["criteria"],
                "level": meta["level"],
                "severity": meta["severity"],
                "expected_result": meta["expected_result"],
                "actual_result": meta["actual_result"],
                "steps_to_reproduce": meta["steps_to_reproduce"],
                "remediation": meta["remediation"],
                "business_impact": meta["business_impact"],
                "html_snippet": "",
                "refined_by": "N/A",
                "help_url": p_help_url,
                "status": "PASS",
                "page_url": str(result.url),
                "page_title": page_title,
                "input_tokens": 0,
                "output_tokens": 0
            })
            counter += 1

    # ── FAILED test cases (violations) ────────────────────────────────────────
    if result.violations:
        for v in result.violations:
            metadata = v.metadata or {}
            nodes = v.nodes or []
            if not isinstance(nodes, list):
                nodes = [nodes]

            # Resolve page context from first node that has it
            page_title = result.metadata.get("page_title", "Page")
            target_url = str(result.url)
            for node in nodes:
                nd = node if isinstance(node, dict) else (
                    node.model_dump(mode='json') if hasattr(node, 'model_dump') else vars(node)
                )
                if nd.get("page_url"):
                    target_url = nd["page_url"]
                if nd.get("page_title") and nd["page_title"] != "N/A":
                    page_title = nd["page_title"]
                break

            # Collect HTML snippets from first 2 nodes
            html_snippets = []
            for node in nodes[:2]:
                nd = node if isinstance(node, dict) else (
                    node.model_dump(mode='json') if hasattr(node, 'model_dump') else vars(node)
                )
                html = nd.get("html", "")
                if html:
                    html_snippets.append(html[:500])
            html_snippet = "\n".join(html_snippets)

            custom_id = generate_tc_custom_id(target_url, page_title, counter)
            testcases.append({
                "testcase_id": custom_id,
                "defect_id": f"DEF-{v.id}",
                "rule_id": v.id,
                "testcase_name": metadata.get("friendly_name", v.help or v.id),
                "description": metadata.get("description", v.description or "N/A"),
                "criteria": metadata.get("wcag_criteria", "N/A"),
                "level": metadata.get("wcag_level", "N/A"),
                "severity": metadata.get("severity", (v.impact or "N/A").capitalize()),
                "expected_result": metadata.get("expected_result", "N/A"),
                "actual_result": metadata.get("actual_result", "N/A"),
                "steps_to_reproduce": metadata.get("steps_to_reproduce", "N/A"),
                "remediation": metadata.get("remediation", "N/A"),
                "business_impact": metadata.get("business_impact", "N/A"),
                "html_snippet": html_snippet,
                "refined_by": metadata.get("refined_by", "N/A"),
                "help_url": getattr(v, "helpUrl", getattr(v, "help_url", "")),
                "status": "FAIL",
                "page_url": target_url,
                "page_title": page_title,
                "input_tokens": metadata.get("input_tokens", 0),
                "output_tokens": metadata.get("output_tokens", 0),
                "screenshot": metadata.get("screenshot", "N/A")
            })
            counter += 1

    reports_dir = get_audit_storage_path(task_id, org_id, proj_id)

    # ── JSON (Minified) ───────────────────────────────────────────────────────
    json_path = os.path.join(reports_dir, f"testcase_report_{task_id}.json")
    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(testcases, f, separators=(',', ':'), ensure_ascii=False)
        print(f"JSON Testcase report saved to {json_path}")
    except Exception as e:
        print(f"Failed to write JSON testcase report: {str(e)}")

    return testcases



# ── Agent Stream Worker Thread ─────────────────────────────────────────────

def start_agent_audit_worker():
    """
    Spawns the background AgentAuditWorker thread.
    """
    thread = threading.Thread(target=_run_agent_audit_worker, daemon=True)
    thread.start()
    logger.info("Agent Audit Worker: Background thread spawned successfully.")


def _run_agent_audit_worker():
    """
    Blocking thread loop that polls the 'crawl:results' Redis stream.
    """
    import time
    time.sleep(2.0)
    logger.info("Agent Audit Worker: Loop started. Listening to stream 'crawl:results'...")
    
    # Listen to new events created after startup
    last_id = "$"
    
    while True:
        try:
            events = read_events("crawl:results", last_id=last_id, block_ms=2000)
            if not events:
                time.sleep(1.0)
                continue
            for msg_id, payload in events:
                last_id = msg_id
                
                task_id = payload.get("task_id")
                url = payload.get("url")
                pages_discovered = payload.get("pages_discovered", [url])
                sitemaps_found = payload.get("sitemaps_found", [])
                error = payload.get("error")
                
                if not task_id or not url:
                    continue
                
                logger.info(f"Agent Audit Worker: Received crawl results for task {task_id} (URLs: {len(pages_discovered)})")
                
                # Retrieve multi-tenant context from existing PostgreSQL session
                db = get_session_local()()
                org_id = None
                proj_id = None
                try:
                    session_rec = db.query(AuditSession).filter_by(task_id=task_id).first()
                    if session_rec:
                        org_id = str(session_rec.organization_id) if session_rec.organization_id else None
                        proj_id = str(session_rec.project_id) if session_rec.project_id else None
                except Exception as db_err:
                    logger.error(f"Agent Audit Worker: Failed to resolve session context for task {task_id}: {db_err}")
                finally:
                    db.close()
                
                # Execute audit scanning in a dedicated event loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    audit_req = AuditRequest(
                        url=url,
                        depth=1,
                        audit_type="standard"
                    )
                    
                    if error:
                        raise Exception(f"Crawl discovery failed downstream: {error}")
                    
                    # Set status to auditing and register pages discovered before scan starts
                    audit_progress_repo.set_status(task_id, "auditing")
                    audit_progress_repo.set_pages(
                        task_id,
                        pages_found=len(pages_discovered),
                        pages_total=len(pages_discovered),
                        pages_discovered=pages_discovered,
                    )
                    
                    loop.run_until_complete(
                        orchestrate_agent_audit(
                            task_id=task_id,
                            request=audit_req,
                            discovered_urls=pages_discovered,
                            sitemaps_found=sitemaps_found,
                            org_id=org_id,
                            proj_id=proj_id
                        )
                    )
                except Exception as run_err:
                    logger.error(f"Agent Audit Worker: Orchestrated audit failed for task {task_id}: {str(run_err)}")
                    # Persist failure states in PostgreSQL
                    audit_progress_repo.mark_failed(task_id, str(run_err), {})
                    
                    db_fail = get_session_local()()
                    try:
                        session_rec = db_fail.query(AuditSession).filter_by(task_id=task_id).first()
                        if session_rec:
                            session_rec.status = "failed"
                            session_rec.summary = {
                                "error": str(run_err),
                                "accessibility_score": 0.0,
                                "total_violations": 0,
                                "passes_count": 0,
                                "token_usage": {}
                            }
                            db_fail.commit()
                    except Exception as fail_db_err:
                        logger.error(f"Agent Audit Worker: Failed to record DB error: {fail_db_err}")
                        db_fail.rollback()
                    finally:
                        db_fail.close()
                finally:
                    loop.close()
                    
        except Exception as e:
            logger.error(f"Agent Audit Worker: Loop error: {str(e)}")
            time.sleep(5.0)


@app.get("/agents/telemetry")
async def get_agents_telemetry():
    db = get_session_local()()
    try:
        active_count = db.query(AuditSession).filter(AuditSession.status.in_(["crawling", "auditing"])).count()
        total_count = db.query(AuditSession).count()
        completed_count = db.query(AuditSession).filter(AuditSession.status == "completed").count()
        failed_count = db.query(AuditSession).filter(AuditSession.status == "failed").count()
        
        # Calculate active tasks from AuditProgress
        active_progress = db.query(AuditProgress).filter(AuditProgress.status.in_(["crawling", "auditing", "processing"])).all()
        active_tasks = []
        for row in active_progress:
            active_tasks.append({
                "task_id": row.task_id,
                "status": row.status,
                "url": row.url,
                "pages_completed": row.pages_completed or 0,
                "pages_total": row.pages_total or 0,
                "created_at": row.created_at.isoformat() if row.created_at else None
            })

        # Sum token usage across completed sessions
        total_input_tokens = 0
        total_output_tokens = 0
        total_tokens = 0
        sessions = db.query(AuditSession).filter(AuditSession.summary.isnot(None)).all()
        for s in sessions:
            summary = s.summary or {}
            tok = summary.get("token_usage", {})
            # Read inner token summaries (supports both flat and nested properties)
            total_input_tokens += tok.get("tokens_sent", 0) or tok.get("tokens_input", 0)
            total_output_tokens += tok.get("tokens_received", 0) or tok.get("tokens_output", 0)
            total_tokens += tok.get("tokens_total", 0) or (tok.get("tokens_sent", 0) + tok.get("tokens_received", 0))

        # Get total violations count
        total_violations = 0
        for s in sessions:
            summary = s.summary or {}
            total_violations += summary.get("total_violations", 0)

        return {
            "active_agents_count": active_count,
            "active_tasks": active_tasks,
            "total_tasks_run": total_count,
            "completed_tasks_run": completed_count,
            "failed_tasks_run": failed_count,
            "total_violations_found": total_violations,
            "tokens": {
                "input_tokens": total_input_tokens,
                "output_tokens": total_output_tokens,
                "total_tokens": total_tokens
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
    finally:
        db.close()


@app.get("/agents/telemetry/stream")
async def stream_agents_telemetry():
    """
    SSE stream of live audit progress telemetry events across the entire cluster.
    """
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


@app.on_event("startup")
async def startup_event():
    """Start background Agent Stream listener thread and clean up stale tasks on service launch."""
    # Clean up tasks stuck in active states from previous runs (older than 2 hours)
    try:
        from datetime import timedelta
        db = get_session_local()()
        cutoff = datetime.utcnow() - timedelta(hours=2)
        stale_sessions = db.query(AuditSession).filter(
            AuditSession.status.in_(["crawling", "auditing"]),
            AuditSession.timestamp < cutoff
        ).all()
        stale_progress = db.query(AuditProgress).filter(
            AuditProgress.status.in_(["crawling", "auditing", "processing"]),
            AuditProgress.created_at < cutoff
        ).all()
        for s in stale_sessions:
            s.status = "failed"
            s.summary = {"error": "Task timed out (stale state cleanup on restart)", "accessibility_score": 0.0, "total_violations": 0, "passes_count": 0, "token_usage": {}}
        for p in stale_progress:
            p.status = "failed"
            p.error = "Task timed out (stale state cleanup on restart)"
        db.commit()
        db.close()
        if stale_sessions or stale_progress:
            logger.info(f"Startup cleanup: marked {len(stale_sessions)} sessions and {len(stale_progress)} progress rows as failed.")
    except Exception as cleanup_err:
        logger.warning(f"Startup stale task cleanup failed: {cleanup_err}")
    
    start_agent_audit_worker()
    try:
        from common.utils.storage_cleanup import start_storage_cleanup_worker
        start_storage_cleanup_worker()
    except Exception as cleanup_err:
        logger.warning(f"Failed to start storage cleanup worker: {cleanup_err}")
