import logging
from typing import List, Tuple
from app.schemas.audit import Violation
from app.schemas.analyze import ScoreBreakdown

logger = logging.getLogger(__name__)

SEVERITY_BUCKETS = {
    "blocker": "critical",
    "critical": "critical",
    "serious": "serious",
    "high": "serious",
    "moderate": "moderate",
    "medium": "moderate",
    "minor": "minor",
    "low": "minor"
}

def get_severity_bucket(impact: str) -> str:
    """
    Maps a raw impact label onto one of the four reporting buckets.
    Defaults to 'moderate' if unknown, matching axe-core's own default.
    """
    if not impact:
        return "moderate"
    return SEVERITY_BUCKETS.get(impact.lower(), "moderate")

def calculate_accessibility_score(violations: List[Violation], passes_count: int = 0) -> Tuple[float, ScoreBreakdown]:
    """
    Calculates the overall accessibility score (0-100) as a pass rate:
    the percentage of accessibility checks (axe-core rules) that passed
    out of all checks that were run on the site.

    This mirrors how compliance is reported to business stakeholders
    (e.g. "82% of accessibility checks passed") instead of an opaque
    penalty formula, making the number directly explainable and
    comparable across audits.

        score = passed_checks / (passed_checks + failed_checks) * 100
    """
    failed_checks = len(violations)
    total_checks = failed_checks + max(0, passes_count)

    score = 100.0 if total_checks == 0 else (passes_count / total_checks) * 100.0
    rounded_score = float(round(score, 1))

    severity_counts = {"critical": 0, "serious": 0, "moderate": 0, "minor": 0}
    for v in violations:
        impact = v.impact or v.metadata.get("severity") or "moderate"
        severity_counts[get_severity_bucket(impact)] += 1

    breakdown = ScoreBreakdown(
        total_checks=total_checks,
        passed_checks=passes_count,
        failed_checks=failed_checks,
        critical_count=severity_counts["critical"],
        serious_count=severity_counts["serious"],
        moderate_count=severity_counts["moderate"],
        minor_count=severity_counts["minor"]
    )

    logger.info(f"Scoring Engine: Pass Rate Score={rounded_score} | Passed={passes_count}/{total_checks}")
    return rounded_score, breakdown
