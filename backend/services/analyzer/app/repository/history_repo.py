"""
HistoryRepository — Handles file-based historical baseline persistence for stateful regression tracking.
"""
import os
import json
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Absolute Path Setup for local persistence storage
STORAGE_DIR = Path(__file__).parent.parent.parent.parent.parent / "storage" / "analyzer_history"


class HistoryRepository:

    def ensure_storage_exists(self) -> None:
        """Ensures that the history database directory is created."""
        try:
            os.makedirs(STORAGE_DIR, exist_ok=True)
        except Exception as e:
            logger.error(f"[HistoryRepository] Failed to create historical storage directory: {str(e)}")

    def get_url_key(self, url: str) -> str:
        """Standardizes a URL and maps it to a safe, unique filename key."""
        parsed = urlparse(url)
        domain = parsed.netloc or "unknown"
        # Scrub port and colons
        domain = domain.split(":")[0]
        
        # Hash the full standardized URL path for specific page/scan differentiation
        url_hash = hashlib.sha256(url.strip().lower().encode("utf-8")).hexdigest()[:16]
        return f"{domain}_{url_hash}"

    def load_previous_audit(self, url: str) -> Optional[Dict[str, Any]]:
        """Loads the last persisted summary for the target URL. Returns None on first run."""
        self.ensure_storage_exists()
        key = self.get_url_key(url)
        file_path = STORAGE_DIR / f"{key}.json"
        
        if not file_path.exists():
            logger.info(f"[HistoryRepository] No past history file found for {url} (Key={key}). First run.")
            return None
            
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"[HistoryRepository] Error reading history file {file_path}: {str(e)}")
            return None

    def save_current_audit(self, url: str, score: float, rule_ids: List[str]) -> None:
        """Persists the current audit details as the new historical baseline for future scans."""
        self.ensure_storage_exists()
        key = self.get_url_key(url)
        file_path = STORAGE_DIR / f"{key}.json"
        
        payload = {
            "url": url,
            "score": score,
            "rule_ids": rule_ids,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            with open(file_path, "w") as f:
                json.dump(payload, f, indent=4)
            logger.info(f"[HistoryRepository] Successfully persisted current baseline summary to {file_path}")
        except Exception as e:
            logger.error(f"[HistoryRepository] Failed to write baseline summary to {file_path}: {str(e)}")


history_repo = HistoryRepository()
