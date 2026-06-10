import asyncio
import sys
import threading
import logging
import time

# Standard fix for Playwright/asyncio subprocesses on Windows
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from common.config import setup_environment, get_cors_origins
# Initialize environment using shared configuration utility
setup_environment()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as crawler_router

# Central event bus utility
from common.utils.event_bus import read_events, publish_event
from app.schemas.crawl import CrawlRequest
from app.core.crawler import WebCrawler

logger = logging.getLogger(__name__)

app = FastAPI(title="A11ySense AI Crawler Service")

from common.exceptions.handler import setup_global_exception_handler
setup_global_exception_handler(app, "crawler-service")

from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app)


app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(crawler_router)


# ── Crawler Stream Worker Thread ───────────────────────────────────────────

def start_crawler_worker():
    """
    Spawns the background CrawlerWorker thread.
    """
    thread = threading.Thread(target=_run_crawler_worker, daemon=True)
    thread.start()
    logger.info("Crawler Worker: Background thread spawned successfully.")


def _run_crawler_worker():
    """
    Blocking thread loop that polls the 'audit:tasks' Redis stream.
    """
    time.sleep(2.0)
    logger.info("Crawler Worker: Loop started. Listening to stream 'audit:tasks'...")
    
    # Listen to new tasks created after service start
    last_id = "$"
    
    while True:
        try:
            events = read_events("audit:tasks", last_id=last_id, block_ms=2000)
            if not events:
                time.sleep(1.0)
                continue
            for msg_id, payload in events:
                last_id = msg_id
                
                task_id = payload.get("task_id")
                url = payload.get("url")
                if not task_id or not url:
                    continue
                
                logger.info(f"Crawler Worker: Received task {task_id} for URL {url}")
                
                # Execute crawl inside dedicated event loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    crawl_req = CrawlRequest(
                        url=url,
                        depth=payload.get("depth", 1),
                        max_pages=payload.get("max_pages", 30),
                        respect_robots_txt=payload.get("respect_robots_txt", True)
                    )
                    crawler = WebCrawler(crawl_req)
                    
                    # Execute crawl asynchronously in this worker loop
                    crawl_res = loop.run_until_complete(crawler.crawl())
                    
                    result_payload = {
                        "task_id": task_id,
                        "url": url,
                        "pages_discovered": crawl_res.pages_discovered,
                        "sitemaps_found": crawl_res.sitemaps_found,
                        "error": None
                    }
                    logger.info(f"Crawler Worker: Completed crawl task {task_id} with {len(crawl_res.pages_discovered)} pages discovered.")
                except Exception as crawl_err:
                    logger.error(f"Crawler Worker: Crawl failed for task {task_id}: {str(crawl_err)}")
                    result_payload = {
                        "task_id": task_id,
                        "url": url,
                        "pages_discovered": [url],
                        "sitemaps_found": [],
                        "error": str(crawl_err)
                    }
                finally:
                    loop.close()
                
                # Publish crawl outcomes onto stream "crawl:results"
                publish_event("crawl:results", result_payload)
                
        except Exception as e:
            logger.error(f"Crawler Worker: Loop error: {str(e)}")
            time.sleep(5.0)


@app.on_event("startup")
async def startup_event():
    """Start the background Crawler Stream subscriber on application launch."""
    start_crawler_worker()
