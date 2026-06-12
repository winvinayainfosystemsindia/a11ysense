"""
History Utility — Backward-compatible delegation wrappers calling history_repo.
"""
import logging
from typing import List, Dict, Any, Optional

from app.schemas.audit import Violation
from app.schemas.analyze import TrendBreakdown
from app.repository.history_repo import history_repo

logger = logging.getLogger(__name__)


def _get_url_key(url: str) -> str:
    """Delegates to the history_repo to standardise and hash the URL."""
    return history_repo.get_url_key(url)


def load_previous_audit(url: str) -> Optional[Dict[str, Any]]:
    """Delegates loading logic to the history_repo."""
    return history_repo.load_previous_audit(url)


def save_current_audit(url: str, score: float, violations: List[Violation]) -> None:
    """Saves baseline audit using rule_ids via history_repo."""
    rule_ids = [v.id for v in violations]
    history_repo.save_current_audit(url, score, rule_ids)


def generate_trend_analysis(url: str, current_score: float, current_violations: List[Violation]) -> TrendBreakdown:
    """
    Compares the current audit metrics against the last recorded run.
    Uses the history_repo to resolve historical summaries.
    """
    previous = history_repo.load_previous_audit(url)
    
    if not previous:
        return TrendBreakdown(
            previous_score=None,
            score_difference=None,
            resolved_violations_count=0,
            new_violations_count=0,
            resolved_rules=[],
            new_rules=[]
        )
        
    prev_score = float(previous.get("score", 100.0))
    prev_rules = set(previous.get("rule_ids", []))
    curr_rules = {v.id for v in current_violations}
    
    # Calculate differentials
    score_diff = float(round(current_score - prev_score, 1))
    resolved = list(prev_rules - curr_rules)
    new_introduced = list(curr_rules - prev_rules)
    
    logger.info(f"Trend Analysis compiled: ScoreDiff={score_diff} | Resolved={len(resolved)} | New={len(new_introduced)}")
    
    return TrendBreakdown(
        previous_score=prev_score,
        score_difference=score_diff,
        resolved_violations_count=len(resolved),
        new_violations_count=len(new_introduced),
        resolved_rules=sorted(resolved),
        new_rules=sorted(new_introduced)
    )
