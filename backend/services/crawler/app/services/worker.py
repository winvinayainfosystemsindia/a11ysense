"""
Worker — Spawns and manages the background Redis listener thread for crawler tasks.
"""
import asyncio
import logging
import threading
import time

from app.services.crawler_service import crawler_service

logger = logging.getLogger(__name__)


def start_crawler_worker() -> None:
    """Spawns the background CrawlerWorker thread."""
    thread = threading.Thread(target=_run_crawler_worker, daemon=True)
    thread.start()
    logger.info("Crawler Worker: Background thread spawned successfully.")


def _run_crawler_worker() -> None:
    """Blocking thread launcher that initializes the async event loop and runs the worker."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_run_crawler_worker_async())
    finally:
        loop.close()


async def _run_crawler_worker_async() -> None:
    """Async listener loop that polls Redis streams for new tasks using the service."""
    await asyncio.sleep(2.0)
    logger.info("Crawler Worker: Loop started. Listening to stream 'audit:tasks'...")
    
    last_id = "$"
    
    while True:
        try:
            last_id, _ = await crawler_service.process_stream_task(last_id)
            await asyncio.sleep(1.0)
        except Exception as e:
            logger.error(f"Crawler Worker: Loop error: {str(e)}")
            await asyncio.sleep(5.0)
