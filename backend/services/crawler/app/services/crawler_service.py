"""
CrawlerService — Handles crawl execution and processes stream tasks.
"""
import asyncio
import logging
from app.schemas.crawl import CrawlRequest, CrawlResponse
from app.core.crawler import WebCrawler
from app.repository.crawler_task_repo import crawler_task_repo

logger = logging.getLogger(__name__)


class CrawlerService:

    async def execute_crawl(self, request: CrawlRequest) -> CrawlResponse:
        """Execute a single crawl job synchronously/asynchronously."""
        if request.crawl_mode == "combined" and request.credential_config:
            return await self._execute_combined_crawl(request)

        if request.credential_config:
            auth_type = request.credential_config.auth_type

            # Form-based auth: crawl_with_playwright() manages its own login browser
            # directly using the same page context it will crawl with. Running a
            # separate login browser here is redundant and injects stale auth headers
            # that cause the login page to redirect before the form can be filled.
            if auth_type != "form":
                from app.repository.auth_repo import auth_repo
                from app.services.login_service import login_service
                import json
                import hashlib

                cred_str = f"{auth_type}:{request.credential_config.login_url}:{request.credential_config.username}"
                cred_hash = hashlib.sha256(cred_str.encode()).hexdigest()
                cache_key = f"crawler:auth:{cred_hash}"

                cached_session = auth_repo.load_session_state(cache_key)
                login_cookies = {}
                login_headers = {}
                landed_url = None
                if cached_session:
                    try:
                        session_data = json.loads(cached_session)
                        login_cookies = session_data.get("cookies", {})
                        login_headers = session_data.get("headers", {})
                        landed_url = session_data.get("landed_url")
                        logger.info("Found cached active authentication session in Redis.")
                    except Exception as e:
                        logger.warning(f"Failed to parse cached session: {e}")
                        cached_session = None

                if not cached_session:
                    success, login_cookies, login_headers, error_detail, landed_url = await login_service.perform_login(request.credential_config)
                    if not success:
                        raise Exception(f"Login failed: {error_detail}")
                    session_data = {
                        "cookies": login_cookies,
                        "headers": login_headers,
                        "landed_url": landed_url
                    }
                    auth_repo.save_session_state(cache_key, json.dumps(session_data))
                    logger.info("Saved new authenticated session to Redis.")

                if not request.cookies:
                    request.cookies = {}
                request.cookies.update(login_cookies)
                if not request.headers:
                    request.headers = {}
                request.headers.update(login_headers)
                if landed_url and not request.landed_url:
                    request.landed_url = landed_url

        crawler = WebCrawler(request)
        return await crawler.crawl()

    async def _execute_combined_crawl(self, request: CrawlRequest) -> CrawlResponse:
        """
        'Both' scan target: crawl once without credentials (public pages) and once
        with credentials (authenticated pages), then merge the discovered sets.
        Run sequentially rather than concurrently so two Playwright contexts don't
        hit the same target at once and trip rate limits/bot detection.
        """
        unauth_request = request.model_copy(update={"credential_config": None, "crawl_mode": "single"})
        unauth_result = await self.execute_crawl(unauth_request)

        auth_request = request.model_copy(update={"crawl_mode": "single"})
        auth_result = await self.execute_crawl(auth_request)

        merged_pages_depth_map = dict(unauth_result.pages_depth_map)
        for url, depth in auth_result.pages_depth_map.items():
            merged_pages_depth_map[url] = min(merged_pages_depth_map.get(url, depth), depth)

        merged_url_to_menu_text = {**unauth_result.url_to_menu_text, **auth_result.url_to_menu_text}
        merged_sitemaps_found = list(set(unauth_result.sitemaps_found) | set(auth_result.sitemaps_found))
        merged_failed_urls = {**unauth_result.failed_urls, **auth_result.failed_urls}
        merged_ignored_urls = list(set(unauth_result.ignored_urls) | set(auth_result.ignored_urls))

        return CrawlResponse(
            start_url=request.url,
            pages_discovered=list(merged_pages_depth_map.keys()),
            pages_with_depth=unauth_result.pages_with_depth + auth_result.pages_with_depth,
            pages_depth_map=merged_pages_depth_map,
            ignored_urls=merged_ignored_urls,
            failed_urls=merged_failed_urls,
            sitemaps_found=merged_sitemaps_found,
            duration_seconds=unauth_result.duration_seconds + auth_result.duration_seconds,
            storage_state=auth_result.storage_state,
            auth_headers=auth_result.auth_headers,
            url_to_menu_text=merged_url_to_menu_text,
            unauth_pages_discovered=unauth_result.pages_discovered,
            auth_pages_discovered=auth_result.pages_discovered,
        )

    async def process_stream_task(self, last_id: str) -> tuple[str, dict]:
        """Polls the task repository for next event, runs the crawl, and publishes results."""
        events = crawler_task_repo.get_next_tasks(last_id, block_ms=2000)
        if not events:
            return last_id, None

        for msg_id, payload in events:
            last_id = msg_id
            task_id = payload.get("task_id")
            url = payload.get("url")
            if not task_id or not url:
                continue

            logger.info(f"Crawler Service: Processing task {task_id} for URL {url}")

            selected_urls = payload.get("selected_urls")

            try:
                if selected_urls:
                    # Pages were already discovered and picked by the user in the
                    # discovery step; skip re-crawling and echo the selection straight
                    # through, carrying forward whatever auth context was passed along.
                    result_payload = {
                        "task_id": task_id,
                        "url": url,
                        "pages_discovered": selected_urls,
                        "sitemaps_found": [],
                        "credential_config": payload.get("credential_config"),
                        "storage_state": payload.get("storage_state"),
                        "auth_headers": payload.get("auth_headers", {}),
                        "pages_depth_map": payload.get("pages_depth_map", {}),
                        "url_to_menu_text": payload.get("url_to_menu_text", {}),
                        "error": None
                    }
                    logger.info(
                        f"Crawler Service: Task {task_id} skipped crawl, using "
                        f"{len(selected_urls)} pre-selected URLs."
                    )
                else:
                    crawl_req = CrawlRequest(
                        url=url,
                        depth=payload.get("depth", 1),
                        max_pages=payload.get("max_pages", 30),
                        respect_robots_txt=payload.get("respect_robots_txt", True),
                        credential_config=payload.get("credential_config")
                    )

                    # Execute crawl
                    crawl_res = await self.execute_crawl(crawl_req)

                    result_payload = {
                        "task_id": task_id,
                        "url": url,
                        "pages_discovered": crawl_res.pages_discovered,
                        "sitemaps_found": crawl_res.sitemaps_found,
                        "credential_config": payload.get("credential_config"),
                        "storage_state": crawl_res.storage_state,
                        "auth_headers": crawl_res.auth_headers,
                        "pages_depth_map": crawl_res.pages_depth_map,
                        "url_to_menu_text": crawl_res.url_to_menu_text,
                        "error": None
                    }
                    logger.info(
                        f"Crawler Service: Completed crawl task {task_id} with "
                        f"{len(crawl_res.pages_discovered)} pages discovered."
                    )
            except Exception as crawl_err:
                logger.error(f"Crawler Service: Crawl failed for task {task_id}: {crawl_err}")
                result_payload = {
                    "task_id": task_id,
                    "url": url,
                    "pages_discovered": [url],
                    "sitemaps_found": [],
                    "credential_config": payload.get("credential_config"),
                    "error": str(crawl_err)
                }

            # Publish result to repo
            crawler_task_repo.publish_crawl_result(result_payload)
            return last_id, result_payload

        return last_id, None


crawler_service = CrawlerService()
