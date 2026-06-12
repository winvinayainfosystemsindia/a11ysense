from fastapi import APIRouter, HTTPException
from app.schemas.crawl import CrawlRequest, CrawlResponse
from app.services.crawler_service import crawler_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/crawl", response_model=CrawlResponse)
async def crawl_site(request: CrawlRequest) -> CrawlResponse:
    """
    Triggers an asynchronous crawl on the target URL with configurations 
    like depth, exclusion patterns, rate limits, strategy, and auth cookies.
    """
    try:
        return await crawler_service.execute_crawl(request)
    except Exception as e:
        logger.exception("Error executing crawl request")
        raise HTTPException(status_code=500, detail=f"Crawl execution failed: {str(e)}")


@router.get("/health")
async def health_check() -> dict:
    """
    Standard microservice health check.
    """
    return {"status": "ok", "service": "crawler-service"}
