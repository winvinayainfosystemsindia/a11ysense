from app.agents.base import BaseAgent
from app.agents.auditor import AuditorAgent
from app.skills.implementations.browser import browser_skill
from app.skills.implementations.scanner import scanner_skill
from app.schemas import AuditRequest, AuditResult
from app.utils.browser import browser_manager
from app.repository.audit_repo import audit_progress_repo
import logging
import os
import httpx
import asyncio

logger = logging.getLogger(__name__)

class ManagerAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="AuditManager", role="Audit Orchestrator")
        self.system_prompt = self.load_prompt("manager.xml")
        self.skills_docs = self.load_skills_docs()
        self.full_system_prompt = f"{self.system_prompt}\n\nAvailable Skills:\n{self.skills_docs}"
        self.auditor = AuditorAgent()

    async def run_audit(
        self,
        request: AuditRequest,
        task_id: str = None,
        pre_discovered_urls: list[str] = None,
        pre_sitemaps_found: list[str] = None
    ) -> AuditResult:
        """
        Orchestrates the multi-agent audit process.
        Supports pre-discovered URLs from the Redis crawl results stream to skip crawl service HTTP calls.
        """
        logger.info(f"ManagerAgent starting audit for {request.url}")

        # 1. Thought Process
        thought_prompt = f"I need to audit {request.url}. What is the plan?"
        thought_response = await self.call_llm(thought_prompt, system_message=self.full_system_prompt, session_id=task_id, agent_type="manager")
        logger.info(f"Manager Thought: {thought_response}")

        # 2. Discover crawlable pages or reuse pre-discovered lists
        sitemaps_found = pre_sitemaps_found or []
        if pre_discovered_urls is not None:
            discovered_urls = pre_discovered_urls
            logger.info(f"Using {len(discovered_urls)} pre-discovered crawl URLs from the event bus.")
        else:
            if task_id:
                audit_progress_repo.set_status(task_id, "crawling")

            discovered_urls = [str(request.url)]
            from common.config import get_service_url
            crawler_service_url = get_service_url("CRAWLER_SERVICE_URL", "http://crawler:8003", "http://localhost:8003")

            if request.depth > 1:
                logger.info(f"Calling crawler service at {crawler_service_url} to discover site structure...")
                try:
                    async with httpx.AsyncClient() as client:
                        payload = {
                            "url": str(request.url),
                            "depth": request.depth,
                            "max_pages": 30,
                            "respect_robots_txt": True
                        }
                        if request.credential_config:
                            payload["credential_config"] = request.credential_config.model_dump(mode="json")
                        response = await client.post(f"{crawler_service_url}/crawl", json=payload, timeout=60.0)
                        response.raise_for_status()
                        crawl_data = response.json()
                        discovered_urls = crawl_data.get("pages_discovered", [str(request.url)])
                        sitemaps_found = crawl_data.get("sitemaps_found", [])
                        logger.info(f"Crawler returned {len(discovered_urls)} pages: {discovered_urls}")
                except Exception as e:
                    logger.error(f"Crawler Service failed, defaulting to start URL: {str(e)}")
            else:
                logger.info("Crawl depth is 1. Skipping crawler service for single page audit.")

        if task_id:
            audit_progress_repo.set_status(task_id, "auditing")
            audit_progress_repo.set_pages(
                task_id,
                pages_found=len(discovered_urls),
                pages_total=len(discovered_urls),
                pages_discovered=discovered_urls,
            )

        # 3. Execution — iterative multi-page scanning
        all_violations = []
        all_passes = []
        all_incomplete = []
        all_inapplicable = []
        pages_summary = {}
        page_title = "Multi-Page Audit"

        for idx, target_url in enumerate(discovered_urls):
            if task_id:
                # Poll DB to check if paused or stopped
                progress = audit_progress_repo.get(task_id)
                if progress:
                    while progress.status == "paused":
                        logger.info(f"Task {task_id} is PAUSED. Waiting 2 seconds...")
                        await asyncio.sleep(2.0)
                        progress = audit_progress_repo.get(task_id)
                        if not progress:
                            break
                    
                    if not progress or progress.status == "stopped":
                        logger.info(f"Task {task_id} is STOPPED/DELETED. Terminating audit iteration.")
                        break

            logger.info(f"Auditing page {idx + 1}/{len(discovered_urls)}: {target_url}")
            try:
                async with browser_manager.get_page() as page:
                    # Navigate
                    await browser_skill.navigate(page, target_url)
                    current_title = await page.title()

                    if idx == 0:
                        page_title = current_title

                    # Run Axe scan ONCE and share results across both agents
                    scan_data = await scanner_skill.run_axe(page)

                    # ── Keyboard Navigation Audit (independent fault-tolerant block) ──
                    try:
                        from app.skills.implementations.keyboard_nav import keyboard_nav_skill
                        logger.info(f"[KB-NAV] Starting keyboard navigation audit on {target_url}...")
                        kb_results = await keyboard_nav_skill.run_keyboard_test(page)
                        kb_violations = kb_results.get("violations", [])
                        kb_passes = kb_results.get("passes", [])
                        scan_data["violations"].extend(kb_violations)
                        scan_data["passes"].extend(kb_passes)
                        logger.info(
                            f"[KB-NAV] Complete — {len(kb_violations)} violation(s), "
                            f"{len(kb_passes)} pass(es) on {target_url}"
                        )
                    except Exception as kb_err:
                        logger.error(
                            f"[KB-NAV] FAILED on {target_url}: {kb_err}",
                            exc_info=True
                        )

                    # ── Screen Reader Simulation Audit (independent fault-tolerant block) ──
                    try:
                        from app.skills.implementations.screen_reader import screen_reader_skill
                        logger.info(f"[SR-SIM] Starting screen reader simulation audit on {target_url}...")
                        sr_results = await screen_reader_skill.run_screen_reader_test(page)
                        sr_violations = sr_results.get("violations", [])
                        sr_passes = sr_results.get("passes", [])
                        scan_data["violations"].extend(sr_violations)
                        scan_data["passes"].extend(sr_passes)
                        logger.info(
                            f"[SR-SIM] Complete — {len(sr_violations)} violation(s), "
                            f"{len(sr_passes)} pass(es) on {target_url}"
                        )
                    except Exception as sr_err:
                        logger.error(
                            f"[SR-SIM] FAILED on {target_url}: {sr_err}",
                            exc_info=True
                        )

                    # Delegate to Technical Auditor (passes pre-scanned data to avoid second scan)
                    violations = await self.auditor.audit_page(
                        page, target_url,
                        session_id=task_id,
                        pre_scan_data=scan_data
                    )

                    # Attach page metadata to each violation node
                    for v in violations:
                        for node in v.nodes:
                            node["page_url"] = target_url
                            node["page_title"] = current_title

                    all_violations.extend(violations)
                    all_passes.extend(scan_data.get("passes", []))
                    all_incomplete.extend(scan_data.get("incomplete", []))
                    all_inapplicable.extend(scan_data.get("inapplicable", []))

                    pages_summary[target_url] = {
                        "title": current_title,
                        "violations_count": len(violations),
                        "passes_count": len(scan_data.get("passes", [])),
                        "status": "success"
                    }
            except Exception as e:
                logger.error(f"Failed to audit page {target_url}: {str(e)}")
                pages_summary[target_url] = {
                    "title": "Failed to load",
                    "violations_count": 0,
                    "passes_count": 0,
                    "status": f"failed: {str(e)}"
                }

            # Persist incremental page progress after each page
            if task_id:
                audit_progress_repo.increment_completed(task_id, target_url)

        # 4. Consolidated Result
        return AuditResult(
            url=request.url,
            violations=all_violations,
            passes=all_passes,
            incomplete=all_incomplete,
            inapplicable=all_inapplicable,
            metadata={
                "page_title": page_title if len(discovered_urls) <= 1 else f"{page_title} (+{len(discovered_urls)-1} pages)",
                "manager_thought": thought_response,
                "summary": {
                    "total_pages_discovered": len(discovered_urls),
                    "total_violations": len(all_violations),
                    "total_passes": len(all_passes),
                    "pages_details": pages_summary,
                    "sitemaps_discovered": sitemaps_found
                },
                "audit_type": "Multi-Page / OpenClaw",
                "engine": "A11ySense-MAS-v1"
            }
        )

