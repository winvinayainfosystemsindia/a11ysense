from common.schemas.audit import AuditResult, Violation
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ScoreBreakdown(BaseModel):
    critical_penalty: float = 0.0
    serious_penalty: float = 0.0
    moderate_penalty: float = 0.0
    minor_penalty: float = 0.0

class TrendBreakdown(BaseModel):
    previous_score: Optional[float] = None
    score_difference: Optional[float] = None
    resolved_violations_count: int = 0
    new_violations_count: int = 0
    resolved_rules: List[str] = []
    new_rules: List[str] = []

class AnalysisResponse(AuditResult):
    accessibility_score: float = 100.0
    score_breakdown: ScoreBreakdown = Field(default_factory=ScoreBreakdown)
    trend: TrendBreakdown = Field(default_factory=TrendBreakdown)
