import math
import logging
from typing import List, Tuple
from app.schemas.audit import Violation
from app.schemas.analyze import ScoreBreakdown

logger = logging.getLogger(__name__)

# Severity Weightings Configuration
SEVERITY_WEIGHTS = {
    "blocker": 10.0,
    "critical": 10.0,
    "serious": 6.0,
    "high": 6.0,
    "moderate": 3.0,
    "medium": 3.0,
    "minor": 1.0,
    "low": 1.0
}

def get_severity_weight(impact: str) -> float:
    """
    Returns the numeric penalty weight for a given issue impact.
    Defaults to 3.0 (moderate) if unknown.
    """
    if not impact:
        return 3.0
    return SEVERITY_WEIGHTS.get(impact.lower(), 3.0)

def calculate_accessibility_score(violations: List[Violation]) -> Tuple[float, ScoreBreakdown]:
    """
    Calculates the overall accessibility score (0-100) using a logarithmic penalty model.
    Deducts points based on rule severity and the logarithmic scale of affected nodes.
    
    Formula:
        penalty = severity_weight * ln(1 + node_count)
        score = max(0, min(100, 100 - sum(penalties)))
    """
    critical_pen = 0.0
    serious_pen = 0.0
    moderate_pen = 0.0
    minor_pen = 0.0
    
    for v in violations:
        # Resolve severity mapping
        impact = v.impact or v.metadata.get("severity") or "moderate"
        weight = get_severity_weight(impact)
        
        # Logarithmic scaling prevents node exhaustion penalties
        node_count = len(v.nodes)
        if node_count == 0:
            continue
            
        penalty = weight * math.log(1.0 + node_count)
        
        # Attribute to breakdown categories
        impact_lower = str(impact).lower()
        if impact_lower in ["blocker", "critical"]:
            critical_pen += penalty
        elif impact_lower in ["serious", "high"]:
            serious_pen += penalty
        elif impact_lower in ["moderate", "medium"]:
            moderate_pen += penalty
        else:
            minor_pen += penalty
            
    total_penalty = critical_pen + serious_pen + moderate_pen + minor_pen
    
    # Calculate score bounded between 0 and 100
    raw_score = 100.0 - total_penalty
    score = max(0.0, min(100.0, raw_score))
    
    # Round metrics for client consumption
    rounded_score = float(round(score, 1))
    
    breakdown = ScoreBreakdown(
        critical_penalty=float(round(critical_pen, 2)),
        serious_penalty=float(round(serious_pen, 2)),
        moderate_penalty=float(round(moderate_pen, 2)),
        minor_penalty=float(round(minor_pen, 2))
    )
    
    logger.info(f"Scoring Engine: Calculated Score={rounded_score} | Total Penalty={total_penalty:.2f}")
    return rounded_score, breakdown
