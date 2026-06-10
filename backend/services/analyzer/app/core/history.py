import os
import json
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from urllib.parse import urlparse

from common.schemas.audit import Violation
from app.schemas.analyze import TrendBreakdown

logger = logging.getLogger(__name__)

# Absolute Path Setup for local persistence storage
STORAGE_DIR = Path(__file__).parent.parent.parent.parent.parent / "storage" / "analyzer_history"

def ensure_storage_exists() -> None:
    """
    Ensures that the history database directory is created.
    """
    try:
        os.makedirs(STORAGE_DIR, exist_ok=True)
    except Exception as e:
        logger.error(f"Failed to create historical storage directory: {str(e)}")

def _get_url_key(url: str) -> str:
    """
    Standardizes a URL and maps it to a safe, unique filename key.
    """
    parsed = urlparse(url)
    domain = parsed.netloc or "unknown"
    # Scrub port and colons
    domain = domain.split(":")[0]
    
    # Hash the full standardized URL path for specific page/scan differentiation
    url_hash = hashlib.sha256(url.strip().lower().encode("utf-8")).hexdigest()[:16]
    return f"{domain}_{url_hash}"

def load_previous_audit(url: str) -> Optional[Dict[str, Any]]:
    """
    Loads the last persisted summary for the target URL. Returns None on first run.
    """
    ensure_storage_exists()
    key = _get_url_key(url)
    file_path = STORAGE_DIR / f"{key}.json"
    
    if not file_path.exists():
        logger.info(f"Trend Analysis: No past history file found for {url} (Key={key}). First run.")
        return None
        
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Trend Analysis: Error reading history file {file_path}: {str(e)}")
        return None

def save_current_audit(url: str, score: float, violations: List[Violation]) -> None:
    """
    Persists the current audit details as the new historical baseline for future scans.
    """
    ensure_storage_exists()
    key = _get_url_key(url)
    file_path = STORAGE_DIR / f"{key}.json"
    
    rule_ids = [v.id for v in violations]
    
    payload = {
        "url": url,
        "score": score,
        "rule_ids": rule_ids,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    try:
        with open(file_path, "w") as f:
            json.dump(payload, f, indent=4)
        logger.info(f"Trend Analysis: Successfully persisted current baseline summary to {file_path}")
    except Exception as e:
        logger.error(f"Trend Analysis: Failed to write baseline summary to {file_path}: {str(e)}")

def generate_trend_analysis(url: str, current_score: float, current_violations: List[Violation]) -> TrendBreakdown:
    """
    Compares the current audit metrics against the last recorded run to compile
    compliance trend statistics.
    """
    previous = load_previous_audit(url)
    
    if not previous:
        # First run yields an empty breakdown baseline
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
