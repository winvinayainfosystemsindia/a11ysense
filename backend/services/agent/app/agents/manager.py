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
        pre_sitemaps_found: list[str] = None,
        pre_storage_state: dict = None,
        pre_auth_headers: dict = None,
        pre_pages_depth_map: dict = None,
        pre_url_to_menu_text: dict = None,
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
        pages_depth_map = pre_pages_depth_map or {}
        crawl_storage_state = None
        crawl_auth_headers = {}
        url_to_menu_text = pre_url_to_menu_text or {}
        
        import urllib.parse
        def local_normalize(url_str: str) -> str:
            try:
                parsed = urllib.parse.urlparse(url_str)
                scheme = parsed.scheme.lower()
                netloc = parsed.netloc.lower()
                if scheme == "http" and netloc.endswith(":80"):
                    netloc = netloc[:-3]
                elif scheme == "https" and netloc.endswith(":443"):
                    netloc = netloc[:-4]
                path = parsed.path
                if not path or path == "/":
                    path = ""
                elif len(path) > 1 and path.endswith("/"):
                    path = path[:-1]
                query = ""
                if parsed.query:
                    params = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
                    params.sort()
                    query = urllib.parse.urlencode(params)
                return urllib.parse.urlunparse((scheme, netloc, path, parsed.params, query, ""))
            except Exception:
                return url_str

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
                        # Authenticated Playwright crawls can take several minutes; allow up to 10 minutes
                        crawl_timeout = 600.0 if request.credential_config else 180.0
                        response = await client.post(f"{crawler_service_url}/crawl", json=payload, timeout=crawl_timeout)
                        response.raise_for_status()
                        crawl_data = response.json()
                        discovered_urls = crawl_data.get("pages_discovered", [str(request.url)])
                        sitemaps_found = crawl_data.get("sitemaps_found", [])
                        crawl_storage_state = crawl_data.get("storage_state")
                        crawl_auth_headers = crawl_data.get("auth_headers", {})
                        pages_depth_map = crawl_data.get("pages_depth_map", {})
                        url_to_menu_text = crawl_data.get("url_to_menu_text", {})
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
                pages_depth_map=pages_depth_map or None,
            )

        # 2.5 Resolve storage_state for authenticated audit pages
        storage_state = pre_storage_state or crawl_storage_state
        auth_headers = pre_auth_headers or crawl_auth_headers or {}
        if request.credential_config and not storage_state:
            # Fallback: if the crawler didn't provide storage_state, perform a login
            from common.config import get_service_url
            crawler_service_url = get_service_url("CRAWLER_SERVICE_URL", "http://crawler:8003", "http://localhost:8003")
            logger.info("No pre-fetched storage_state. Falling back to /login for audit context...")
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{crawler_service_url}/login",
                        json=request.credential_config.model_dump(mode="json"),
                        timeout=30.0
                    )
                    response.raise_for_status()
                    login_data = response.json()
                    storage_state = login_data.get("storage_state")
                    auth_headers = login_data.get("headers", {})
                    logger.info("Successfully retrieved storage state from login fallback.")
            except Exception as e:
                logger.error(f"Failed to perform login fallback for audit context: {e}")
        elif storage_state:
            logger.info("Using pre-fetched storage_state from crawler response (no second login needed).")

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
                # Use guest context (no auth) for the login page, and authenticated context for other pages
                is_login_page = False
                if request.credential_config:
                    target_clean = target_url.strip().lower().rstrip("/")
                    login_clean = request.credential_config.login_url.strip().lower().rstrip("/")
                    if target_clean == login_clean:
                        is_login_page = True
                        
                current_storage_state = None if is_login_page else storage_state
                current_auth_headers = {} if is_login_page else auth_headers
                
                async with browser_manager.get_page(storage_state=current_storage_state, extra_http_headers=current_auth_headers or None) as page:
                    # Determine how to navigate to the target URL
                    target_url_norm = local_normalize(target_url)
                    target_menu_text = url_to_menu_text.get(target_url_norm) if url_to_menu_text else None
                    
                    if target_menu_text and target_url_norm != local_normalize(str(request.url)):
                        logger.info(f"Using client-side navigation. Loading entrypoint URL first: {request.url}")
                        await browser_skill.navigate(page, str(request.url))
                        
                        # Wait for entrypoint to be ready
                        try:
                            await page.wait_for_selector("[class*='loader'], [class*='spinner'], [id*='loader'], [id*='spinner'], :has-text('Loading')", state="hidden", timeout=15000)
                        except Exception:
                            pass
                        try:
                            await page.wait_for_selector("li, nav a, aside a, main, #root, #app", state="visible", timeout=15000)
                            await page.wait_for_timeout(3000)
                        except Exception:
                            await page.wait_for_timeout(5000)
                        
                        # Click the menu item client-side
                        logger.info(f"Clicking menu item '{target_menu_text}' to navigate client-side to {target_url}")
                        clicked = await page.evaluate("""(targetMenuText) => {
                            const targetSel = 'nav [role="button"], aside [role="button"], ' +
                                '.MuiDrawer-root [role="button"], .MuiList-root [role="button"], ' +
                                'nav button, aside button, [role="navigation"] [role="button"], ' +
                                'nav a, aside a, .MuiDrawer-root a';
                            const elts = document.querySelectorAll(targetSel);
                            
                            // First, try to find the menu item directly
                            for (const el of elts) {
                                const t = (el.textContent || '').replace(/\\s+/g, ' ').trim();
                                if (t === targetMenuText) {
                                    el.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));
                                    return true;
                                }
                            }
                            
                            // If it's not found directly (maybe sub-menu is collapsed), expand all collapsed toggles
                            for (const el of elts) {
                                const isExpanded = el.getAttribute('aria-expanded') === 'true' || 
                                                   el.classList.contains('Mui-expanded');
                                if (!isExpanded) {
                                    el.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));
                                }
                            }
                            
                            // Try again
                            const reElts = document.querySelectorAll(targetSel);
                            for (const el of reElts) {
                                const t = (el.textContent || '').replace(/\\s+/g, ' ').trim();
                                if (t === targetMenuText) {
                                    el.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));
                                    return true;
                                }
                            }
                            return false;
                        }""", target_menu_text)
                        
                        if clicked:
                            await page.wait_for_timeout(3000)
                            # Wait for loaders on the new page
                            try:
                                await page.wait_for_selector("[class*='loader'], [class*='spinner'], [id*='loader'], [id*='spinner'], :has-text('Loading')", state="hidden", timeout=15000)
                            except Exception:
                                pass
                            
                            current_url_norm = local_normalize(page.url)
                            if current_url_norm != target_url_norm:
                                logger.warning(f"Client-side navigation clicked, but URL is {page.url} instead of {target_url}. Falling back to direct page.goto.")
                                await browser_skill.navigate(page, target_url)
                        else:
                            logger.warning(f"Could not click menu item '{target_menu_text}'. Falling back to direct page.goto.")
                            await browser_skill.navigate(page, target_url)
                    else:
                        # Fallback to direct navigation
                        await browser_skill.navigate(page, target_url)

                    # Wait for React SPA to render and load completely (disappearing spinners, loading text)
                    try:
                        await page.wait_for_selector("[class*='loader'], [class*='spinner'], [id*='loader'], [id*='spinner'], :has-text('Loading')", state="hidden", timeout=15000)
                    except Exception:
                        pass
                    # Wait for navigation/content elements to be visible
                    try:
                        await page.wait_for_selector("li, nav a, aside a, main, #root, #app", state="visible", timeout=15000)
                        # Give it a moment to finish rendering
                        await page.wait_for_timeout(3000)
                    except Exception:
                        await page.wait_for_timeout(5000)

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

