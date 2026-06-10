from fastapi import APIRouter, HTTPException
from app.schemas.crawl import CrawlRequest, CrawlResponse
from app.core.crawler import WebCrawler
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/crawl", response_model=CrawlResponse)
async def crawl_site(request: CrawlRequest):
    """
    Triggers an asynchronous crawl on the target URL with configurations 
    like depth, exclusion patterns, rate limits, strategy, and auth cookies.
    """
    try:
        crawler = WebCrawler(request)
        response = await crawler.crawl()
        return response
    except Exception as e:
        logger.exception("Error executing crawl request")
        raise HTTPException(status_code=500, detail=f"Crawl execution failed: {str(e)}")

@router.get("/health")
async def health_check():
    """
    Standard microservice health check.
    """
    return {"status": "ok", "service": "crawler-service"}
