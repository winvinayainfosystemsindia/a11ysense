"""
Worker — Spawns and manages the background Redis listener thread for crawling results.
"""
import asyncio
import logging
import threading
import time

from app.schemas import AuditRequest
from app.repository.audit_repo import audit_progress_repo
from app.repository.session_repo import audit_session_repo
from app.services.orchestrator import audit_orchestrator

from common.utils.event_bus import read_events

logger = logging.getLogger(__name__)


def start_agent_audit_worker() -> None:
    """Spawns the background AgentAuditWorker thread."""
    thread = threading.Thread(target=_run_agent_audit_worker, daemon=True)
    thread.start()
    logger.info("Agent Audit Worker: Background thread spawned successfully.")


def _run_agent_audit_worker() -> None:
    """Blocking thread loop that polls the 'crawl:results' Redis stream."""
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
                org_id = None
                proj_id = None
                try:
                    session_rec = audit_session_repo.get_session_by_task_id(task_id)
                    if session_rec:
                        org_id = str(session_rec.get("organization_id")) if session_rec.get("organization_id") else None
                        proj_id = str(session_rec.get("project_id")) if session_rec.get("project_id") else None
                except Exception as db_err:
                    logger.error(f"Agent Audit Worker: Failed to resolve session context for task {task_id}: {db_err}")
                
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
                        audit_orchestrator.orchestrate_agent_audit(
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
                    try:
                        audit_session_repo.mark_session_failed(task_id, str(run_err), {})
                    except Exception as fail_db_err:
                        logger.error(f"Agent Audit Worker: Failed to record DB error: {fail_db_err}")
                finally:
                    loop.close()
                    
        except Exception as e:
            logger.error(f"Agent Audit Worker: Loop error: {str(e)}")
            time.sleep(5.0)
