from fastapi import APIRouter, HTTPException
import logging
from app.schemas.audit import AuditResult
from app.schemas.analyze import AnalysisResponse
from app.core.heuristics import aggregate_and_deduplicate
from app.core.scoring import calculate_accessibility_score
from app.core.history import generate_trend_analysis, save_current_audit

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_violations(result: AuditResult):
    """
    Core compliance analysis endpoint.
    De-duplicates, pre-filters, scores, and tracks regressions statefully.
    """
    try:
        logger.info(f"Analyzer Service: Starting analysis for URL: {result.url}")
        
        # 1. Cross-page de-duplication and heuristic pre-filtering
        deduped_violations = aggregate_and_deduplicate(result.violations)
        
        # 2. Weighted scoring calculations
        score, breakdown = calculate_accessibility_score(deduped_violations)
        
        # 3. Trend analysis delta compilation
        trend = generate_trend_analysis(result.url, score, deduped_violations)
        
        # 4. Save current baseline for regression tracking on subsequent scans
        save_current_audit(result.url, score, deduped_violations)
        
        logger.info(f"Analyzer Service: Completed analysis for {result.url}. Score: {score}/100")
        
        return AnalysisResponse(
            url=result.url,
            timestamp=result.timestamp,
            violations=deduped_violations,
            passes=result.passes or [],
            incomplete=result.incomplete or [],
            inapplicable=result.inapplicable or [],
            accessibility_score=score,
            score_breakdown=breakdown,
            trend=trend,
            metadata=result.metadata
        )
    except Exception as e:
        logger.exception(f"Analyzer failed to process results for {result.url}")
        raise HTTPException(status_code=500, detail=f"Analyzer processing error: {str(e)}")

@router.get("/health")
async def health_check():
    """
    Microservice health indicator.
    """
    return {"status": "ok", "service": "analyzer-service"}
