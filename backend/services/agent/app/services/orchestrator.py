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

from app.schemas import AuditRequest, AuditTask, AuditResult, Violation
from app.agents.manager import ManagerAgent
from app.repository.audit_repo import audit_progress_repo
from app.repository.session_repo import audit_session_repo

from common.config import get_service_url, get_storage_path, get_audit_storage_path
from common.utils.event_bus import publish_event, get_redis_client
from common.constants import parse_wcag_tags

logger = logging.getLogger(__name__)
manager_agent = ManagerAgent()
REPORTING_SERVICE_URL = get_service_url("REPORTING_SERVICE_URL", "http://reporting:8002", "http://localhost:8002")


class AuditOrchestrator:

    async def fetch_and_format_token_usage(self, task_id: str) -> dict:
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
        
        if request.depth > 1:
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
                    if request.credential_config:
                        payload["credential_config"] = request.credential_config.model_dump(mode="json")
                    crawl_timeout = 300.0 if request.credential_config else 60.0
                    response = await client.post(f"{crawler_service_url}/crawl", json=payload, timeout=crawl_timeout)
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

        try:
            write_debug(f"Orchestrating multi-agent audit scanning for URLs: {discovered_urls}")
            await self.orchestrate_agent_audit(
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
        proj_id: Optional[str] = None
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
                pre_sitemaps_found=sitemaps_found
            )

            # Route raw results to Analyzer Service
            ANALYZER_SERVICE_URL = get_service_url("ANALYZER_SERVICE_URL", "http://analyzer:8004", "http://localhost:8004")
            try:
                logger.info(f"Routing raw compliance results to central Analyzer Service: {ANALYZER_SERVICE_URL}")
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

                    refined_result.violations = [Violation(**v) for v in analyzed_data.get("violations", [])]
                    refined_result.metadata["accessibility_score"] = analyzed_data.get("accessibility_score", 100.0)
                    refined_result.metadata["score_breakdown"] = analyzed_data.get("score_breakdown", {})
                    refined_result.metadata["trend"] = analyzed_data.get("trend", {})
                    logger.info(f"Analyzer Service resolved (Score={refined_result.metadata['accessibility_score']})")
            except Exception as e:
                logger.error(f"Analyzer Service unavailable, falling back: {str(e)}")

            # Compile final token usage report
            token_usage = await self.fetch_and_format_token_usage(task_id)
            refined_result.metadata["token_usage"] = token_usage

            report_url = f"http://localhost:8002/report/{task_id}"

            # Compile and save testcase reports
            try:
                await self.compile_and_save_testcase_report(task_id, refined_result, org_id=org_id, proj_id=proj_id)
            except Exception as tc_err:
                logger.error(f"Failed to generate testcase report: {str(tc_err)}")

            # Check if stopped early by user
            final_progress = audit_progress_repo.get(task_id)
            is_stopped = final_progress and final_progress.status == "stopped"

            # Publish the finalized audit result onto stream "audit:analyzed"
            if get_redis_client() is not None:
                try:
                    publish_event("audit:analyzed", {
                        "task_id": task_id,
                        "result": refined_result.model_dump(mode='json'),
                        "report_url": report_url
                    })
                except Exception as pub_err:
                    logger.warning(f"Failed to publish audit:analyzed event: {pub_err}")

            # Direct reporting service trigger fallback if Redis is down
            if get_redis_client() is None:
                try:
                    logger.info(f"Redis is down. Directly POSTing report payload to Reporting Service: {REPORTING_SERVICE_URL}")
                    async with httpx.AsyncClient() as client:
                        reporting_response = await client.post(
                            f"{REPORTING_SERVICE_URL}/generate",
                            params={"task_id": task_id},
                            json=refined_result.model_dump(mode='json'),
                            headers=headers,
                            timeout=30.0
                        )
                        reporting_response.raise_for_status()
                        logger.info(f"Reporting Service successfully compiled Allure report for task {task_id}")
                except Exception as report_err:
                    logger.error(f"Failed to compile Allure report over direct HTTP fallback: {str(report_err)}")

            # Deduct billing credits
            pages_crawled = len(discovered_urls)
            pages_scanned = len(refined_result.metadata.get("summary", {}).get("pages_details", {}))
            if pages_scanned == 0:
                pages_scanned = pages_crawled
            
            credits_spent = pages_crawled + (5 * pages_scanned)
            
            if org_id:
                try:
                    from common.billing.billing_manager import billing_manager
                    from common.database.connection import get_session_local
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
                        logger.error(f"Failed to deduct billing credits: {billing_err}")
                    finally:
                        db_billing.close()
                except Exception as import_err:
                    logger.error(f"Billing Manager import failed: {import_err}")

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
                "token_usage": token_usage
            }

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
        progress_row = audit_progress_repo.create(task_id, str(request.url))

        # Bootstrap AuditSession record
        try:
            audit_session_repo.bootstrap_session(task_id, str(request.url), org_id, proj_id)
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

        if get_redis_client() is not None:
            publish_event("audit:tasks", task_payload)
        else:
            logger.info(f"Redis is offline. Triggering audit for task {task_id} in-memory via BackgroundTasks.")
            background_tasks.add_task(
                self.run_in_memory_audit_flow,
                task_id=task_id,
                request=request,
                org_id=org_id,
                proj_id=proj_id
            )

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
            report_url = f"http://localhost:8002/report/{task_id}" if session_rec.get("status") == "completed" else None

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
                summary=summary
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
                meta = self.resolve_passed_metadata(p_id, p_tags, p_desc, p_help, p_metadata)
                
                page_title = result.metadata.get("page_title", "Page")
                custom_id = self.generate_tc_custom_id(result.url, page_title, counter)
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

                html_snippets = []
                for node in nodes[:2]:
                    nd = node if isinstance(node, dict) else (
                        node.model_dump(mode='json') if hasattr(node, 'model_dump') else vars(node)
                    )
                    html = nd.get("html", "")
                    if html:
                        html_snippets.append(html[:500])
                html_snippet = "\n".join(html_snippets)

                custom_id = self.generate_tc_custom_id(target_url, page_title, counter)
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
        json_path = os.path.join(reports_dir, f"testcase_report_{task_id}.json")
        try:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(testcases, f, separators=(',', ':'), ensure_ascii=False)
            logger.info(f"JSON Testcase report saved to {json_path}")
        except Exception as e:
            logger.error(f"Failed to write JSON testcase report: {str(e)}")

        return testcases


audit_orchestrator = AuditOrchestrator()
