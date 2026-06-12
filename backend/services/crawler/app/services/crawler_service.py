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
        crawler = WebCrawler(request)
        return await crawler.crawl()

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

            try:
                crawl_req = CrawlRequest(
                    url=url,
                    depth=payload.get("depth", 1),
                    max_pages=payload.get("max_pages", 30),
                    respect_robots_txt=payload.get("respect_robots_txt", True)
                )
                
                # Execute crawl
                crawl_res = await self.execute_crawl(crawl_req)
                
                result_payload = {
                    "task_id": task_id,
                    "url": url,
                    "pages_discovered": crawl_res.pages_discovered,
                    "sitemaps_found": crawl_res.sitemaps_found,
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
                    "error": str(crawl_err)
                }

            # Publish result to repo
            crawler_task_repo.publish_crawl_result(result_payload)
            return last_id, result_payload

        return last_id, None


crawler_service = CrawlerService()
