"""
CrawlDiscoveryOrchestrator — runs the standalone "discover pages" step
(decoupled from auditing) so the user can pick which pages to audit afterward.
"""
import logging
from typing import Optional

from common.config import get_service_url
from common.schemas.audit import CrawlDiscoveryRequest, CrawlDiscoveryTask
from app.repository.crawl_progress_repo import crawl_progress_repo

logger = logging.getLogger(__name__)

UNLIMITED_DEPTH = 999
DISCOVERY_MAX_PAGES = 300

CRAWLER_SERVICE_URL = get_service_url("CRAWLER_SERVICE_URL", "http://crawler:8003", "http://localhost:8003")


class CrawlDiscoveryOrchestrator:

    async def start_discovery(
        self,
        request: CrawlDiscoveryRequest,
        org_id: Optional[str],
        proj_id: Optional[str],
        background_tasks
    ) -> CrawlDiscoveryTask:
        import uuid
        crawl_task_id = str(uuid.uuid4())

        task = crawl_progress_repo.create(crawl_task_id, request.url, request.scan_target, org_id, proj_id)

        background_tasks.add_task(self._run_discovery, crawl_task_id, request)

        return task

    async def _run_discovery(self, crawl_task_id: str, request: CrawlDiscoveryRequest) -> None:
        import httpx

        crawl_progress_repo.set_status(crawl_task_id, "crawling")

        wants_auth = request.scan_target in ("web_application", "both")
        crawl_mode = "combined" if request.scan_target == "both" else "single"

        try:
            payload = {
                "url": request.url,
                "depth": UNLIMITED_DEPTH,
                "max_pages": DISCOVERY_MAX_PAGES,
                "respect_robots_txt": True,
                "crawl_mode": crawl_mode,
            }
            if wants_auth and request.credential_config:
                payload["credential_config"] = request.credential_config.model_dump(mode="json")

            crawl_timeout = 600.0 if wants_auth and request.credential_config else 180.0

            async with httpx.AsyncClient() as client:
                response = await client.post(f"{CRAWLER_SERVICE_URL}/crawl", json=payload, timeout=crawl_timeout)
                response.raise_for_status()
                data = response.json()

            crawl_progress_repo.set_result(
                crawl_task_id,
                pages_discovered=data.get("pages_discovered", [request.url]),
                pages_depth_map=data.get("pages_depth_map", {}),
                url_to_menu_text=data.get("url_to_menu_text", {}),
                sitemaps_found=data.get("sitemaps_found", []),
                unauth_pages_discovered=data.get("unauth_pages_discovered", []),
                auth_pages_discovered=data.get("auth_pages_discovered", []),
                storage_state=data.get("storage_state"),
                auth_headers=data.get("auth_headers", {}),
            )
            logger.info(f"Crawl discovery {crawl_task_id} completed with {len(data.get('pages_discovered', []))} pages.")
        except Exception as e:
            logger.error(f"Crawl discovery {crawl_task_id} failed: {e}")
            crawl_progress_repo.mark_failed(crawl_task_id, str(e))

    async def get_status(self, crawl_task_id: str) -> CrawlDiscoveryTask:
        task = crawl_progress_repo.get(crawl_task_id)
        if task:
            return task
        return CrawlDiscoveryTask(crawl_task_id=crawl_task_id, status="not_found", url="")


crawl_discovery_orchestrator = CrawlDiscoveryOrchestrator()
