from fastapi import APIRouter, HTTPException
from app.schemas.crawl import CrawlRequest, CrawlResponse
from app.services.crawler_service import crawler_service
from common.schemas.audit import PageCredentialConfig
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


@router.post("/test_login")
async def test_login(config: PageCredentialConfig) -> dict:
    """
    Validates a login configuration using Playwright without performing a full crawl.
    """
    try:
        from app.services.login_service import login_service
        success, cookies, headers, error_detail = await login_service.perform_login(config)
        if not success:
            raise HTTPException(status_code=400, detail=error_detail or "Login failed.")
        return {
            "status": "success",
            "message": "Login successful.",
            "cookies_count": len(cookies),
            "headers_count": len(headers)
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.exception("Error executing test login")
        raise HTTPException(status_code=500, detail=f"Login test failed: {str(e)}")


@router.get("/health")
async def health_check() -> dict:
    """
    Standard microservice health check.
    """
    return {"status": "ok", "service": "crawler-service"}

