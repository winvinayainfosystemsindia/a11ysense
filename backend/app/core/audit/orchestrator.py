"""
AuditOrchestrator — Service for managing audit runs, background flows, token usages, and reports.
"""
import asyncio
import json
import logging
import os
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse

from fastapi.responses import StreamingResponse

from common.schemas.audit import AuditRequest, AuditTask, AuditResult, Violation
from backend.app.core.audit.manager import ManagerAgent
from backend.app.repository.audit_repo import audit_progress_repo
from backend.app.repository.session_repo import audit_session_repo
from backend.app.repository.crawl_progress_repo import crawl_progress_repo

from common.config import get_service_url, get_storage_path, get_audit_storage_path
from common.utils.event_bus import publish_event, get_redis_client
from common.constants import parse_wcag_tags, A11YSENSE_AUDIT_SCOPE, A11YSENSE_MANUAL_REVIEW_CRITERIA, _AUDIT_SCOPE_CODES, WCAG_CRITERIA_MAP
from common.constants.rule_catalog import resolve_rule, normalize_severity, principle_for
from common.constants.sc_catalog import SC_CATALOG
from backend.app.core.reporting.narrative import fallback_narrative
from backend.app.core.reporting.quality_gate import check_report

logger = logging.getLogger(__name__)
manager_agent = ManagerAgent()


class AuditOrchestrator:

    async def run_crawl_discovery_flow(
        self,
        crawl_task_id: str,
        request: Any,
        org_id: Optional[str] = None,
        proj_id: Optional[str] = None
    ):
        """Runs page discovery crawl and updates CrawlProgress DB record."""
        from common.schemas.crawl import CrawlRequest
        from backend.app.core.crawler.crawler import WebCrawler

        try:
            crawl_progress_repo.set_status(crawl_task_id, "crawling")
            
            crawl_req = CrawlRequest(
                url=request.url,
                depth=3,
                max_pages=50,
                credential_config=getattr(request, "credential_config", None)
            )
            crawler = WebCrawler(crawl_req)
            result = await crawler.crawl()

            pages_discovered = result.pages_discovered or [request.url]
            pages_depth_map = result.pages_depth_map or {request.url: 1}
            url_to_menu_text = result.url_to_menu_text or {}
            sitemaps_found = result.sitemaps_found or []

            unauth = []
            auth = []
            if result.pages_with_depth:
                for pd in result.pages_with_depth:
                    if pd.is_authenticated:
                        auth.append(pd.url)
                    else:
                        unauth.append(pd.url)
            else:
                unauth = pages_discovered

            crawl_progress_repo.set_result(
                crawl_task_id,
                pages_discovered=pages_discovered,
                pages_depth_map=pages_depth_map,
                url_to_menu_text=url_to_menu_text,
                sitemaps_found=sitemaps_found,
                unauth_pages_discovered=unauth,
                auth_pages_discovered=auth,
                storage_state=result.storage_state,
                auth_headers=result.auth_headers
            )
            logger.info(f"Crawl discovery task {crawl_task_id} completed successfully ({len(pages_discovered)} pages discovered).")
        except Exception as e:
            logger.error(f"Crawl discovery task {crawl_task_id} failed: {e}")
            crawl_progress_repo.mark_failed(crawl_task_id, str(e))

    async def fetch_and_format_token_usage(self, task_id: str) -> dict:
        """Fetch token usage from the LLM service for the given task."""
        progress = audit_progress_repo.get(task_id)
        url = progress.url if progress else ""
        created_at_dt = progress.created_at if progress else None
        audited_at = created_at_dt.isoformat() if created_at_dt else datetime.utcnow().isoformat()

        # In-process token summary from progress record
        tokens_sent = 0
        tokens_received = 0
        tokens_total = 0
        llm_calls = 0
        provider = "mock"
        breakdown = {}

        if progress and getattr(progress, "token_usage", None):
            tok = progress.token_usage
            provider = tok.get("provider", "mock")
            tokens_sent = tok.get("tokens_sent", 0)
            tokens_received = tok.get("tokens_received", 0)
            tokens_total = tok.get("tokens_total", 0)
            llm_calls = tok.get("llm_calls", 0)
            breakdown = tok.get("breakdown", {})

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
        self,
        task_id: str,
        request: AuditRequest,
        org_id: Optional[str] = None,
        proj_id: Optional[str] = None
    ):
        """Bypasses Redis and runs the crawl and audit sequence in-memory using BackgroundTasks."""
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
        crawl_storage_state = None
        crawl_auth_headers = {}
        crawl_depth_map = {}
        crawl_url_to_menu_text = {}
        
        if request.selected_urls:
            discovered_urls = request.selected_urls
            write_debug(f"Using {len(discovered_urls)} pre-selected URLs from the discovery step; skipping crawler call.")
            if request.crawl_task_id:
                auth_context = crawl_progress_repo.get_auth_context(request.crawl_task_id)
                if auth_context:
                    crawl_storage_state = auth_context.get("storage_state")
                    crawl_auth_headers = auth_context.get("auth_headers") or {}
                    crawl_depth_map = auth_context.get("pages_depth_map") or {}
                    crawl_url_to_menu_text = auth_context.get("url_to_menu_text") or {}
                    sitemaps_found = auth_context.get("sitemaps_found") or []
                    write_debug("Recovered auth context (storage_state/auth_headers) from prior crawl discovery.")
        elif request.depth > 1:
            try:
                write_debug(f"Executing in-process crawler for depth {request.depth}...")
                from common.schemas.crawl import CrawlRequest
                from backend.app.core.crawler.crawler import WebCrawler
                crawl_req = CrawlRequest(
                    url=str(request.url),
                    depth=request.depth,
                    max_pages=30,
                    credential_config=request.credential_config
                )
                crawler = WebCrawler(crawl_req)
                crawl_data = await crawler.crawl()
                discovered_urls = crawl_data.pages_discovered or [str(request.url)]
                sitemaps_found = crawl_data.sitemaps_found or []
                crawl_storage_state = crawl_data.storage_state
                crawl_auth_headers = crawl_data.auth_headers or {}
                crawl_depth_map = crawl_data.pages_depth_map or {}
                crawl_url_to_menu_text = crawl_data.url_to_menu_text or {}
                write_debug(f"In-process crawler completed. Discovered {len(discovered_urls)} URLs: {discovered_urls}")
            except Exception as e:
                err_trace = traceback.format_exc()
                write_debug(f"In-process crawl failed: {str(e)}\nTraceback:\n{err_trace}")
                crawl_error = str(e)
        else:
            write_debug("Crawl depth is 1. Skipping crawler call.")

        try:
            write_debug("Updating DB states to auditing...")
            audit_progress_repo.set_status(task_id, "auditing")
            audit_progress_repo.set_pages(
                task_id,
                pages_found=len(discovered_urls),
                pages_total=len(discovered_urls),
                pages_discovered=discovered_urls,
                pages_depth_map=crawl_depth_map or None,
            )
            write_debug("DB states updated to auditing successfully.")
        except Exception as e:
            err_trace = traceback.format_exc()
            write_debug(f"Failed to update progress status to auditing: {str(e)}\nTrace:\n{err_trace}")

        if crawl_error and request.depth > 1 and len(discovered_urls) <= 1:
            write_debug("Crawl discovery failed with no pages found, marking task as failed in DB...")
            audit_progress_repo.mark_failed(task_id, f"Crawl discovery failed downstream: {crawl_error}", {})
            try:
                audit_session_repo.mark_session_failed(task_id, f"Crawl discovery failed downstream: {crawl_error}", {})
                write_debug("Recorded fail state in DB successfully.")
            except Exception as fail_db_err:
                write_debug(f"Failed to record fail state in DB: {fail_db_err}")
            return
        elif crawl_error:
            write_debug(f"Non-fatal crawl warning: {crawl_error}. Proceeding with {len(discovered_urls)} discovered URL(s).")

        # Global task timeout: max 1 hour total for the whole audit (configurable via env)
        TASK_TIMEOUT_SECONDS = int(os.getenv("AUDIT_TASK_TIMEOUT_SECONDS", "3600"))

        try:
            write_debug(f"Orchestrating multi-agent audit scanning for URLs: {discovered_urls}")
            await asyncio.wait_for(
                self.orchestrate_agent_audit(
                    task_id=task_id,
                    request=request,
                    discovered_urls=discovered_urls,
                    sitemaps_found=sitemaps_found,
                    org_id=org_id,
                    proj_id=proj_id,
                    storage_state=crawl_storage_state,
                    auth_headers=crawl_auth_headers,
                    pages_depth_map=crawl_depth_map,
                    url_to_menu_text=crawl_url_to_menu_text,
                ),
                timeout=TASK_TIMEOUT_SECONDS
            )
            write_debug("Orchestrated audit completed successfully.")
        except asyncio.TimeoutError:
            timeout_msg = f"Audit task timed out after {TASK_TIMEOUT_SECONDS // 60} minutes. Please retry."
            write_debug(f"TASK TIMEOUT: {timeout_msg}")
            logger.error(f"Task {task_id} exceeded global timeout of {TASK_TIMEOUT_SECONDS}s. Marking as failed.")
            audit_progress_repo.mark_failed(task_id, timeout_msg, {})
            try:
                audit_session_repo.mark_session_failed(task_id, timeout_msg, {})
            except Exception as fail_db_err:
                write_debug(f"Failed to record timeout failure in DB: {fail_db_err}")
        except Exception as run_err:
            err_trace = traceback.format_exc()
            write_debug(f"Orchestrated audit failed: {str(run_err)}\nTrace:\n{err_trace}")
            audit_progress_repo.mark_failed(task_id, str(run_err), {})
            try:
                audit_session_repo.mark_session_failed(task_id, str(run_err), {})
                write_debug("Recorded audit failure in DB successfully.")
            except Exception as fail_db_err:
                write_debug(f"Failed to record audit failure in DB: {fail_db_err}")

    async def orchestrate_agent_audit(
        self,
        task_id: str,
        request: AuditRequest,
        discovered_urls: List[str],
        sitemaps_found: List[str],
        org_id: Optional[str] = None,
        proj_id: Optional[str] = None,
        storage_state: Optional[Dict] = None,
        auth_headers: Optional[Dict[str, str]] = None,
        pages_depth_map: Optional[Dict[str, int]] = None,
        url_to_menu_text: Optional[Dict[str, str]] = None,
    ):
        """Execute the Multi-Agent Audit using pre-discovered URLs."""
        import httpx
        from common.utils.correlation import get_correlation_headers
        headers = get_correlation_headers()

        # Mark AuditSession as auditing
        try:
            audit_session_repo.update_session_status(task_id, "auditing")
        except Exception as pg_err:
            logger.error(f"Failed to update session status to auditing in DB: {str(pg_err)}")

        try:
            refined_result = await manager_agent.run_audit(
                request,
                task_id=task_id,
                pre_discovered_urls=discovered_urls,
                pre_sitemaps_found=sitemaps_found,
                pre_storage_state=storage_state,
                pre_auth_headers=auth_headers,
                pre_pages_depth_map=pages_depth_map,
                pre_url_to_menu_text=url_to_menu_text,
            )

            # Direct in-process Analyzer calculation
            passes_cnt = len(refined_result.passes or [])
            viols_cnt = len(refined_result.violations or [])
            tot_rules = passes_cnt + viols_cnt
            score = round((passes_cnt / tot_rules) * 100, 1) if tot_rules > 0 else 100.0
            refined_result.metadata["accessibility_score"] = score
            refined_result.metadata["score_breakdown"] = {
                "passes": passes_cnt,
                "violations": viols_cnt,
                "total": tot_rules
            }
            refined_result.metadata["trend"] = {"status": "stable"}
            logger.info(f"In-process Compliance Analysis resolved (Score={score})")

            # Calculate WCAG criteria coverage
            covered_a = set()
            covered_aa = set()
            
            def _extract_criteria_code(rule) -> str | None:
                tags = []
                if isinstance(rule, dict):
                    tags = rule.get("tags", [])
                elif hasattr(rule, "tags"):
                    tags = getattr(rule, "tags", [])
                elif hasattr(rule, "model_dump"):
                    tags = rule.model_dump().get("tags", [])
                criteria, _ = parse_wcag_tags(tags)
                if criteria != "N/A":
                    code = criteria.split(" ")[0]
                    if code in _AUDIT_SCOPE_CODES:
                        return code
                return None

            for rule_list in [refined_result.passes, refined_result.violations]:
                for r in (rule_list or []):
                    code = _extract_criteria_code(r)
                    if code:
                        scope_entry = next((s for s in A11YSENSE_AUDIT_SCOPE if s["code"] == code), None)
                        if scope_entry:
                            if scope_entry["level"] == "A":
                                covered_a.add(code)
                            elif scope_entry["level"] == "AA":
                                covered_aa.add(code)

            # Mark manual review and N/A criteria
            refined_result.metadata["criteria_coverage"] = {
                "covered_a": list(covered_a),
                "covered_aa": list(covered_aa),
                "manual_review": [c["code"] for c in A11YSENSE_MANUAL_REVIEW_CRITERIA],
                "not_applicable": [c["code"] for c in A11YSENSE_AUDIT_SCOPE if c["code"] not in covered_a and c["code"] not in covered_aa and c["code"] not in [m["code"] for m in A11YSENSE_MANUAL_REVIEW_CRITERIA]]
            }

            wcag_stats = {
                "level_a_covered": len(covered_a),
                "level_a_total": 19,
                "level_aa_covered": len(covered_aa),
                "level_aa_total": 7
            }
            refined_result.metadata["wcag_stats"] = wcag_stats

            # Compile final token usage report
            token_usage = await self.fetch_and_format_token_usage(task_id)
            refined_result.metadata["token_usage"] = token_usage

            report_url = f"/api/reports/excel/{task_id}"

            # Compile and save testcase reports
            testcases = []
            try:
                testcases = await self.compile_and_save_testcase_report(task_id, refined_result, org_id=org_id, proj_id=proj_id)
            except Exception as tc_err:
                logger.error(f"Failed to generate testcase report: {str(tc_err)}")

            # Check if stopped early by user
            final_progress = audit_progress_repo.get(task_id)
            is_stopped = final_progress and final_progress.status == "stopped"

            # Publish the finalized audit result onto stream "audit:analyzed" if Redis is available
            if get_redis_client() is not None:
                try:
                    publish_event("audit:analyzed", {
                        "task_id": task_id,
                        "result": refined_result.model_dump(mode='json'),
                        "report_url": report_url
                    })
                except Exception as pub_err:
                    logger.warning(f"Failed to publish audit:analyzed event: {pub_err}")

            # Persist summary + violations
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
                "token_usage": token_usage,
                "wcag_stats": wcag_stats,
                "test_cases": testcases
            }

            # Save summary_data to summary_{task_id}.json in reports storage
            try:
                reports_dir = get_audit_storage_path(task_id, org_id, proj_id)
                summary_path = os.path.join(reports_dir, f"summary_{task_id}.json")
                with open(summary_path, "w", encoding="utf-8") as f:
                    json.dump(summary_data, f, indent=2)
                logger.info(f"Saved summary JSON to {summary_path}")
            except Exception as summary_file_err:
                logger.error(f"Failed to write summary JSON file: {summary_file_err}")

            try:
                status = "stopped" if is_stopped else "completed"
                audit_session_repo.save_session_results(
                    task_id=task_id,
                    status=status,
                    summary_data=summary_data,
                    violations=refined_result.violations or []
                )
                logger.info(f"Task {task_id} successfully persisted in PostgreSQL.")
            except Exception as pg_commit_err:
                logger.error(f"Failed to commit complete audit result to PostgreSQL: {str(pg_commit_err)}")

            # Mark progress as completed or stopped
            if is_stopped:
                audit_progress_repo.set_status(task_id, "stopped")
            else:
                audit_progress_repo.mark_completed(task_id, token_usage, report_url)

            logger.info(f"Task {task_id} completed successfully.")

        except Exception as e:
            logger.error(f"Error in task {task_id}: {str(e)}")

            # Fetch and store token usage even on failure
            try:
                token_usage = await self.fetch_and_format_token_usage(task_id)
            except Exception:
                token_usage = {}

            # Mark progress as failed
            audit_progress_repo.mark_failed(task_id, str(e), token_usage)

            # Push to Redis DLQ
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
                    logger.info(f"Task {task_id} failure pushed to Redis DLQ 'audit:dlq'.")
                except Exception as dlq_err:
                    logger.error(f"Failed to push task failure to Redis DLQ: {str(dlq_err)}")
            else:
                logger.warning(f"Redis unavailable — skipping DLQ push for failed task {task_id}.")

            # Update AuditSession status to failed
            try:
                audit_session_repo.mark_session_failed(task_id, str(e), token_usage)
            except Exception as pg_fail_err:
                logger.error(f"Failed to update failed status in PostgreSQL: {str(pg_fail_err)}")

    async def start_audit(
        self,
        request: AuditRequest,
        org_id: Optional[str],
        proj_id: Optional[str],
        background_tasks
    ) -> AuditTask:
        """Start a new audit flow and dispatch via Redis Stream or in-memory tasks."""
        task_id = str(uuid.uuid4())

        # Write initial AuditProgress row
        progress_row = audit_progress_repo.create(task_id, str(request.url), request.depth)

        # Bootstrap AuditSession record
        try:
            audit_session_repo.bootstrap_session(task_id, str(request.url), org_id, proj_id, request.depth)
        except Exception as db_err:
            logger.error(f"Failed to bootstrap audit session: {db_err}")

        # Set progress status to crawling
        audit_progress_repo.set_status(task_id, "crawling")

        task_payload = {
            "task_id": task_id,
            "url": str(request.url),
            "depth": request.depth,
            "audit_type": request.audit_type,
            "org_id": org_id,
            "proj_id": proj_id
        }
        if request.credential_config:
            task_payload["credential_config"] = request.credential_config.model_dump(mode="json")
        if request.selected_urls:
            task_payload["selected_urls"] = request.selected_urls
        if request.crawl_task_id:
            task_payload["crawl_task_id"] = request.crawl_task_id
            # Carry forward the auth session captured during discovery so the crawler
            # worker can skip re-crawling and the audit phase still authenticates correctly.
            auth_context = crawl_progress_repo.get_auth_context(request.crawl_task_id)
            if auth_context:
                if auth_context.get("storage_state"):
                    task_payload["storage_state"] = auth_context["storage_state"]
                if auth_context.get("auth_headers"):
                    task_payload["auth_headers"] = auth_context["auth_headers"]
                if auth_context.get("pages_depth_map"):
                    task_payload["pages_depth_map"] = auth_context["pages_depth_map"]
                if auth_context.get("url_to_menu_text"):
                    task_payload["url_to_menu_text"] = auth_context["url_to_menu_text"]

        if get_redis_client() is not None:
            publish_event("audit:tasks", task_payload)
        else:
            logger.info(f"Redis is offline. Triggering audit for task {task_id} via isolated background thread.")
            import threading

            def _run_in_thread():
                """Run the async audit in its own event loop, isolated from the Uvicorn event loop.
                This prevents a hung Playwright call from blocking the /status/{task_id} endpoint.
                """
                import sys
                if sys.platform == "win32":
                    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
                    loop = asyncio.ProactorEventLoop()
                else:
                    loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(
                        self.run_in_memory_audit_flow(
                            task_id=task_id,
                            request=request,
                            org_id=org_id,
                            proj_id=proj_id
                        )
                    )
                except Exception as thread_err:
                    logger.error(f"Background audit thread failed for task {task_id}: {thread_err}")
                    audit_progress_repo.mark_failed(task_id, str(thread_err), {})
                    try:
                        audit_session_repo.mark_session_failed(task_id, str(thread_err), {})
                    except Exception:
                        pass
                finally:
                    # Clean up the Playwright browser for this thread
                    try:
                        from app.utils.browser import browser_manager
                        loop.run_until_complete(browser_manager.stop())
                    except Exception:
                        pass
                    loop.close()

            t = threading.Thread(target=_run_in_thread, daemon=True, name=f"audit-{task_id[:8]}")
            t.start()

        return audit_progress_repo.as_audit_task(task_id) or progress_row

    async def get_status(self, task_id: str) -> AuditTask:
        """Returns the current audit status. Reads from AuditProgress, with fallback to AuditSession."""
        audit_task = audit_progress_repo.as_audit_task(task_id)
        if audit_task:
            if audit_task.status in ["completed", "failed", "stopped"]:
                session_rec = audit_session_repo.get_session_by_task_id(task_id)
                if session_rec:
                    audit_task.summary = session_rec.get("summary")
            else:
                # Enrich token usage if still running
                try:
                    audit_task.token_usage = await self.fetch_and_format_token_usage(task_id)
                except Exception:
                    pass
            return audit_task

        # Fallback to AuditSession table (summary after completion)
        session_rec = audit_session_repo.get_session_by_task_id(task_id)
        if session_rec:
            summary = session_rec.get("summary") or {}
            passes_count = summary.get("passes_count", 0)
            total_violations = summary.get("total_violations", 0)
            pages_total = passes_count + total_violations
            report_url = f"/api/reports/excel/{task_id}" if session_rec.get("status") == "completed" else None

            return AuditTask(
                task_id=task_id,
                status=session_rec.get("status"),
                url=session_rec.get("url"),
                created_at=session_rec.get("timestamp"),
                report_url=report_url,
                pages_found=pages_total,
                pages_completed=pages_total,
                pages_total=pages_total,
                pages_scanned=[session_rec.get("url")] if session_rec.get("status") == "completed" else [],
                pages_discovered=[session_rec.get("url")] if session_rec.get("status") == "completed" else [],
                error=summary.get("error"),
                token_usage=summary.get("token_usage"),
                summary=summary,
                depth=session_rec.get("depth", 1)
            )

        return AuditTask(task_id=task_id, status="not_found")

    async def stream_task_status(self, task_id: str) -> StreamingResponse:
        """Server-Sent Events (SSE) stream for real-time audit progress."""
        async def event_generator():
            while True:
                row = audit_progress_repo.get(task_id)
                if row is None:
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

                if task_data.status in ["completed", "failed"]:
                    break

                await asyncio.sleep(1.5)

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            }
        )

    async def get_status_token_usage(self, task_id: str) -> dict:
        """Return LLM token usage. Reads from AuditProgress if completed, else fetches live."""
        row = audit_progress_repo.get(task_id)
        if row and row.token_usage:
            return row.token_usage
        return await self.fetch_and_format_token_usage(task_id)

    async def stop_audit(self, task_id: str) -> dict:
        """Stop a running audit task."""
        progress = audit_progress_repo.get(task_id)
        if not progress:
            return {}
        audit_progress_repo.set_status(task_id, "stopped")
        audit_session_repo.update_session_status(task_id, "stopped")
        return {"status": "stopped", "task_id": task_id}

    async def pause_audit(self, task_id: str) -> dict:
        """Pause a running audit task."""
        progress = audit_progress_repo.get(task_id)
        if not progress:
            return {}
        audit_progress_repo.set_status(task_id, "paused")
        audit_session_repo.update_session_status(task_id, "paused")
        return {"status": "paused", "task_id": task_id}

    async def resume_audit(self, task_id: str) -> dict:
        """Resume a paused audit task."""
        progress = audit_progress_repo.get(task_id)
        if not progress:
            return {}
        new_status = "auditing" if progress.pages_found > 0 else "crawling"
        audit_progress_repo.set_status(task_id, new_status)
        audit_session_repo.update_session_status(task_id, new_status)
        return {"status": new_status, "task_id": task_id}

    async def delete_audit(self, task_id: str) -> dict:
        """Delete progress row for a task_id."""
        audit_progress_repo.delete(task_id)
        return {"status": "deleted", "task_id": task_id}

    async def get_testcase_report(self, task_id: str) -> list:
        """Retrieve testcase report data from disk."""
        reports_dir = get_audit_storage_path(task_id)
        json_path = os.path.join(reports_dir, f"testcase_report_{task_id}.json")
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    # ── Testcase report compiling helpers ──────────────────────────────────────

    def generate_tc_custom_id(self, url: str, page_title: str, counter: int) -> str:
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
        return f"TC-{website}-{title}-{counter_str}"

    def resolve_passed_metadata(self, p_id: str, tags: list, p_desc: str, p_help: str, p_metadata: dict = None) -> dict:
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

        criteria, level = parse_wcag_tags(tags)
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

    async def compile_and_save_testcase_report(self, task_id: str, result, org_id: str = None, proj_id: str = None) -> list:
        base_page_url = str(result.url) if result.url else ""
        base_page_title = (result.metadata or {}).get("page_title", "Page") if hasattr(result, "metadata") and result.metadata else "Page"
        pass_mode = os.getenv("REPORT_PASS_MODE", "per_criterion").lower()

        fail_testcases: list = []
        seen_fail_cases: dict = {}

        # ── 1. FAILED test cases (violations) ─────────────────────────────────
        # 1 unique element = 1 testcase = (rule_id, normalized_element_html, page_url)
        # Duplicate elements on the same page are merged with repeat_count and remarks
        if getattr(result, "violations", None):
            for v in result.violations:
                v_id = v.get("id", "") if isinstance(v, dict) else getattr(v, "id", "")
                rule = resolve_rule(v_id)
                v_meta = v.get("metadata") if isinstance(v, dict) else getattr(v, "metadata", None)
                v_meta = v_meta or {}

                raw_nodes = v.get("nodes") if isinstance(v, dict) else getattr(v, "nodes", None)
                if not raw_nodes:
                    raw_nodes = [{"html": "", "target": []}]
                elif not isinstance(raw_nodes, list):
                    raw_nodes = [raw_nodes]

                for nd in raw_nodes:
                    node_dict = nd if isinstance(nd, dict) else (
                        nd.model_dump(mode='json') if hasattr(nd, 'model_dump') else vars(nd)
                    )
                    raw_html = node_dict.get("html", "") or ""
                    norm_html = " ".join(raw_html.strip().split())
                    target_sel = node_dict.get("target", []) or []

                    node_page_url = node_dict.get("page_url") or getattr(v, "page_url", None) or base_page_url
                    node_page_title = node_dict.get("page_title") or base_page_title

                    dedup_key = (v_id, norm_html, node_page_url)
                    if dedup_key in seen_fail_cases:
                        existing = seen_fail_cases[dedup_key]
                        existing["repeat_count"] += 1
                        existing["remarks"] = f"Same problem found {existing['repeat_count']} times on this page."
                        continue

                    # Retrieve narrative: prefer refined metadata if complete, else fallback_narrative
                    has_refined = bool(
                        v_meta.get("description")
                        and v_meta.get("expected_result")
                        and v_meta.get("actual_result")
                        and v_meta.get("steps_to_reproduce")
                    )

                    if has_refined:
                        desc = v_meta.get("description", "")
                        expected = v_meta.get("expected_result", "")
                        actual = v_meta.get("actual_result", "")
                        steps = v_meta.get("steps_to_reproduce", "")
                        if isinstance(steps, list):
                            steps = "\n".join(f"{i+1}. {s}" for i, s in enumerate(steps))
                        friendly_name = v_meta.get("friendly_name") or rule.title
                        business_impact = v_meta.get("business_impact", "")
                        fix_steps = v_meta.get("fix_steps") or []
                        remediation = v_meta.get("remediation") or ("\n".join(fix_steps) if fix_steps else "")
                        code_before = v_meta.get("code_before", "")
                        code_after = v_meta.get("code_after", "")
                        verify_steps = v_meta.get("verify_steps") or []
                        false_pos = v_meta.get("false_positive_note", "")
                        screenshot = v_meta.get("screenshot", "N/A")
                        refined_by = v_meta.get("refined_by", "rule_catalog")
                    else:
                        fb = fallback_narrative(rule, raw_html)
                        desc = fb["description"]
                        expected = fb["expected_result"]
                        actual = fb["actual_result"]
                        steps = "\n".join(f"{i+1}. {s}" for i, s in enumerate(fb["steps_to_reproduce"])) if isinstance(fb["steps_to_reproduce"], list) else fb["steps_to_reproduce"]
                        friendly_name = fb["friendly_name"]
                        business_impact = fb["business_impact"]
                        fix_steps = fb["fix_steps"]
                        remediation = "\n".join(fix_steps)
                        code_before = fb["code_before"]
                        code_after = fb["code_after"]
                        verify_steps = fb["verify_steps"]
                        false_pos = fb["false_positive_note"]
                        screenshot = "N/A"
                        refined_by = "fallback_template"

                    # Deterministic facts from rule_catalog
                    criteria_str = rule.get("criteria", "N/A")
                    rule_level = rule.get("level", "A")
                    rule_principle = rule.get("principle", "N/A")
                    rule_severity = rule.get("severity", "Serious")
                    tc_record = {
                        "rule_id": v_id,
                        "testcase_name": friendly_name,
                        "description": desc,
                        "criteria": criteria_str,
                        "level": rule_level,
                        "principle": rule_principle,
                        "severity": rule_severity,
                        "expected_result": expected,
                        "actual_result": actual,
                        "steps_to_reproduce": steps,
                        "remediation": remediation,
                        "business_impact": business_impact,
                        "html_snippet": raw_html[:500] if raw_html else "N/A",
                        "status": "FAIL",
                        "page_url": node_page_url,
                        "page_title": node_page_title,
                        "screenshot": screenshot,
                        "repeat_count": 1,
                        "remarks": "",
                        "fix_steps": fix_steps,
                        "code_before": code_before,
                        "code_after": code_after,
                        "verify_steps": verify_steps,
                        "false_positive_note": false_pos,
                        "input_tokens": v_meta.get("input_tokens", 0),
                        "output_tokens": v_meta.get("output_tokens", 0),
                        "help_url": getattr(v, "helpUrl", getattr(v, "help_url", "")),
                        "refined_by": refined_by
                    }
                    seen_fail_cases[dedup_key] = tc_record
                    fail_testcases.append(tc_record)

        # ── 2. Determine criteria status for the 26 automated scope criteria ──
        failed_sc_codes = {tc["criteria"].split(" ")[0] for tc in fail_testcases}

        passed_sc_map: Dict[str, list] = {}
        if getattr(result, "passes", None):
            for p in result.passes:
                p_id = p.get('id', '') if isinstance(p, dict) else getattr(p, 'id', '')
                p_rule = resolve_rule(p_id)
                sc_code = p_rule.get("sc_code")
                if sc_code:
                    passed_sc_map.setdefault(sc_code, []).append(p)

        pass_testcases: list = []
        na_testcases: list = []

        if pass_mode == "per_element" and getattr(result, "passes", None):
            # Per-element pass mode
            for p in result.passes:
                p_id = p.get('id', 'Unknown') if isinstance(p, dict) else getattr(p, 'id', 'Unknown')
                p_rule = resolve_rule(p_id)
                p_nodes = p.get('nodes', []) if isinstance(p, dict) else getattr(p, 'nodes', [])
                if not isinstance(p_nodes, list):
                    p_nodes = [p_nodes]
                if not p_nodes:
                    p_nodes = [{"html": "", "target": []}]

                for nd in p_nodes:
                    nd_dict = nd if isinstance(nd, dict) else (
                        nd.model_dump(mode='json') if hasattr(nd, 'model_dump') else vars(nd)
                    )
                    raw_html = nd_dict.get("html", "") or ""
                    p_url = nd_dict.get("page_url") or (p.get('page_url') if isinstance(p, dict) else getattr(p, 'page_url', None)) or base_page_url
                    p_title = nd_dict.get("page_title") or (p.get('page_title') if isinstance(p, dict) else getattr(p, 'page_title', None)) or base_page_title
                    sc_code = p_rule.get("sc_code") or "1.1.1"
                    sc_info = SC_CATALOG.get(sc_code, {})

                    pass_testcases.append({
                        "rule_id": p_id,
                        "testcase_name": p_rule.get("criteria", p_id),
                        "description": sc_info.get("what_we_check", f"Verify element meets {p_rule.get('criteria', 'accessibility')} requirements."),
                        "criteria": p_rule.get("criteria", "N/A"),
                        "level": p_rule.get("level", "A"),
                        "principle": p_rule.get("principle", "N/A"),
                        "severity": "N/A",
                        "expected_result": sc_info.get("expected", f"Elements on the page should comply with WCAG {p_rule.wcag_sc} {p_rule.wcag_sc_name}."),
                        "actual_result": "Verification passed: Element meets accessibility requirements.",
                        "steps_to_reproduce": "1. Open webpage.\n2. Locate element.\n3. Verify element complies with accessibility requirements.",
                        "remediation": "No remediation required. Element complies with accessibility requirements.",
                        "business_impact": f"Ensures optimal user experience for {p_rule.wcag_sc_name}.",
                        "html_snippet": raw_html[:500] if raw_html else "N/A",
                        "status": "PASS",
                        "page_url": p_url,
                        "page_title": p_title,
                        "screenshot": "N/A",
                        "repeat_count": 1,
                        "remarks": "",
                        "fix_steps": [],
                        "code_before": "",
                        "code_after": "",
                        "verify_steps": [],
                        "false_positive_note": "",
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "help_url": getattr(p, "helpUrl", getattr(p, "help_url", "")),
                        "refined_by": "rule_catalog"
                    })
        else:
            # per_criterion pass mode (default)
            for scope_crit in A11YSENSE_AUDIT_SCOPE:
                code = scope_crit["code"]
                if code in failed_sc_codes:
                    continue  # Already represented by FAIL test case(s)
                elif code in passed_sc_map:
                    p_list = passed_sc_map[code]
                    elem_count = 0
                    for p in p_list:
                        nds = p.get('nodes', []) if isinstance(p, dict) else getattr(p, 'nodes', [])
                        elem_count += len(nds) if isinstance(nds, list) else 1
                    elem_count = max(elem_count, 1)

                    sc_info = SC_CATALOG.get(code, {})
                    actual_msg = (
                        f"All {elem_count} elements checked on this page meet this requirement."
                        if elem_count > 1
                        else "All elements checked on this page meet this requirement."
                    )
                    pass_testcases.append({
                        "rule_id": f"wcag-{code}",
                        "testcase_name": scope_crit["name"],
                        "description": sc_info.get("what_we_check", f"Verify elements meet WCAG {code} {scope_crit['name']} requirements."),
                        "criteria": f"{code} {scope_crit['name']}",
                        "level": scope_crit["level"],
                        "principle": principle_for(code),
                        "severity": "N/A",
                        "expected_result": sc_info.get("expected", f"All elements on the page should comply with WCAG {code} {scope_crit['name']}."),
                        "actual_result": actual_msg,
                        "steps_to_reproduce": "1. Open the webpage in a browser.\n2. Locate elements matching this requirement.\n3. Verify all elements meet accessibility standards.",
                        "remediation": "No remediation required. Elements comply with accessibility requirements.",
                        "business_impact": f"Ensures accessible user experience for {scope_crit['name']}.",
                        "html_snippet": "N/A",
                        "status": "PASS",
                        "page_url": base_page_url,
                        "page_title": base_page_title,
                        "screenshot": "N/A",
                        "repeat_count": 1,
                        "remarks": "",
                        "fix_steps": [],
                        "code_before": "",
                        "code_after": "",
                        "verify_steps": [],
                        "false_positive_note": "",
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "help_url": f"https://www.w3.org/WAI/WCAG22/Understanding/{code.replace('.', '')}",
                        "refined_by": "rule_catalog"
                    })
                else:
                    # NOT_APPLICABLE: 0 failing, 0 passing elements
                    sc_info = SC_CATALOG.get(code, {})
                    na_testcases.append({
                        "rule_id": f"wcag-{code}",
                        "testcase_name": scope_crit["name"],
                        "description": f"WCAG {code} {scope_crit['name']} — No elements matching this criterion were found on the audited pages.",
                        "criteria": f"{code} {scope_crit['name']}",
                        "level": scope_crit["level"],
                        "principle": principle_for(code),
                        "severity": "N/A",
                        "expected_result": sc_info.get("expected", f"Elements on the page should comply with WCAG {code} {scope_crit['name']}."),
                        "actual_result": "No elements matching this criterion were found on the website. This criterion is not applicable for this audit.",
                        "steps_to_reproduce": "N/A",
                        "remediation": "No action required. This criterion did not apply to the audited pages.",
                        "business_impact": "N/A",
                        "html_snippet": "N/A",
                        "status": "NOT_APPLICABLE",
                        "page_url": base_page_url,
                        "page_title": base_page_title,
                        "screenshot": "N/A",
                        "repeat_count": 1,
                        "remarks": "",
                        "fix_steps": [],
                        "code_before": "",
                        "code_after": "",
                        "verify_steps": [],
                        "false_positive_note": "",
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "help_url": "",
                        "refined_by": "rule_catalog"
                    })

        # ── 3. MANUAL_REVIEW entries for the 24 criteria not covered by the tool ──
        manual_testcases: list = []
        for manual_crit in A11YSENSE_MANUAL_REVIEW_CRITERIA:
            code = manual_crit["code"]
            sc_info = SC_CATALOG.get(code, {})
            manual_steps = sc_info.get("manual_steps", [])
            steps_str = (
                "\n".join(f"{i+1}. {s}" for i, s in enumerate(manual_steps))
                if manual_steps
                else "1. Open the page in a browser.\n2. Perform manual review with assistive technology."
            )
            manual_testcases.append({
                "rule_id": f"wcag-{code}",
                "testcase_name": manual_crit["name"],
                "description": sc_info.get("what_we_check", f"WCAG {code} {manual_crit['name']} — Requires manual human testing."),
                "criteria": f"{code} {manual_crit['name']}",
                "level": manual_crit["level"],
                "principle": principle_for(code),
                "severity": "N/A",
                "expected_result": sc_info.get("expected", f"Elements on the page should comply with WCAG {code} {manual_crit['name']}."),
                "actual_result": f"This criterion requires human judgment and is not covered by the automated audit tool.\n\nRecommended verification steps:\n{steps_str}",
                "steps_to_reproduce": steps_str,
                "remediation": "Perform manual accessibility verification with real assistive technology (screen readers, keyboard, screen magnifier) and human testers.",
                "business_impact": f"Manual review ensures full WCAG 2.1 Level A and AA compliance for {manual_crit['name']}.",
                "html_snippet": "N/A",
                "status": "MANUAL_REVIEW",
                "page_url": "All pages",
                "page_title": "All pages",
                "screenshot": "N/A",
                "repeat_count": 1,
                "remarks": "Manual review required",
                "fix_steps": manual_steps,
                "code_before": "",
                "code_after": "",
                "verify_steps": manual_steps,
                "false_positive_note": "",
                "input_tokens": 0,
                "output_tokens": 0,
                "help_url": f"https://www.w3.org/WAI/WCAG22/Understanding/{code.replace('.', '')}",
                "refined_by": "rule_catalog"
            })

        # ── 4. Combine all into ordered testcases list and assign sequential IDs ──
        all_testcases = fail_testcases + pass_testcases + na_testcases + manual_testcases

        tc_counter = 0
        def_counter = 0
        for tc in all_testcases:
            tc_counter += 1
            tc["testcase_id"] = f"TC-{tc_counter:04d}"
            custom_id = self.generate_tc_custom_id(tc["page_url"], tc["page_title"], tc_counter)
            tc["display_name"] = custom_id

            if tc["status"] == "FAIL":
                def_counter += 1
                tc["defect_id"] = f"DEF-{def_counter:04d}"
            else:
                tc["defect_id"] = "N/A"

        # ── 5. Save JSON report to disk ───────────────────────────────────────
        reports_dir = get_audit_storage_path(task_id, org_id, proj_id)
        json_path = os.path.join(reports_dir, f"testcase_report_{task_id}.json")
        try:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(all_testcases, f, separators=(',', ':'), ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to write JSON testcase report: {str(e)}")

        # ── 6. Run Quality Gate Validation ───────────────────────────────────
        try:
            qg_issues = check_report(all_testcases)
            if qg_issues:
                error_issues = [i for i in qg_issues if i.severity == "ERROR"]
                if error_issues:
                    logger.warning(f"Quality Gate found {len(error_issues)} ERRORs in testcase report {task_id}: {[i.message for i in error_issues[:3]]}")
                else:
                    logger.info(f"Quality Gate passed with {len(qg_issues)} warnings for task {task_id}")
            else:
                logger.info(f"Quality Gate passed with 0 issues for task {task_id}")
        except Exception as qg_err:
            logger.error(f"Quality Gate execution failed for task {task_id}: {str(qg_err)}")

        return all_testcases


audit_orchestrator = AuditOrchestrator()
