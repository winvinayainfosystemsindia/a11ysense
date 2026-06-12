from fastapi import APIRouter, HTTPException
import logging
from app.schemas.audit import AuditResult
from app.schemas.analyze import AnalysisResponse
from app.services.analysis_service import analysis_service

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_violations(result: AuditResult):
    """
    Core compliance analysis endpoint.
    Delegates all analysis tasks to the AnalysisService.
    """
    try:
        logger.info(f"Analyzer Service: Starting analysis for URL: {result.url}")
        return await analysis_service.analyze_violations(result)
    except Exception as e:
        logger.exception(f"Analyzer failed to process results for {result.url}")
        raise HTTPException(status_code=500, detail=f"Analyzer processing error: {str(e)}")

@router.get("/health")
async def health_check():
    """
    Microservice health indicator.
    """
    return {"status": "ok", "service": "analyzer-service"}
