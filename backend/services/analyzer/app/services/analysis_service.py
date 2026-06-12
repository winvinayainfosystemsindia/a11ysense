"""
AnalysisService — Orchestrates the accessibility audit analysis processing.
"""
import logging
from app.schemas.audit import AuditResult
from app.schemas.analyze import AnalysisResponse
from app.core.heuristics import aggregate_and_deduplicate
from app.core.scoring import calculate_accessibility_score
from app.core.history import generate_trend_analysis, save_current_audit

logger = logging.getLogger(__name__)


class AnalysisService:

    async def analyze_violations(self, result: AuditResult) -> AnalysisResponse:
        """
        Core compliance analysis logic.
        De-duplicates, pre-filters, scores, and tracks regressions statefully.
        """
        # 1. Cross-page de-duplication and heuristic pre-filtering
        deduped_violations = aggregate_and_deduplicate(result.violations)
        
        # 2. Weighted scoring calculations
        score, breakdown = calculate_accessibility_score(deduped_violations)
        
        # 3. Trend analysis delta compilation (delegates historical loading to repo via wrappers)
        trend = generate_trend_analysis(result.url, score, deduped_violations)
        
        # 4. Save current baseline for regression tracking (delegates persistence to repo via wrappers)
        save_current_audit(result.url, score, deduped_violations)
        
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


analysis_service = AnalysisService()
