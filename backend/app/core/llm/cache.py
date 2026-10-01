"""
LLM Response Caching Module using DiskCache.
"""
import hashlib
import json
import logging
from typing import Optional, Dict, Any
from backend.app.cache import get_cache

logger = logging.getLogger(__name__)

class LLMCache:
    def __init__(self, ttl: int = 86400 * 7):  # Default 7 days cache TTL
        self.cache = get_cache()
        self.ttl = ttl

    def _generate_key(self, prompt: str, system_message: str = "", provider: str = "", vision: bool = False) -> str:
        data = f"{provider}:{vision}:{system_message}:{prompt}"
        hash_digest = hashlib.sha256(data.encode("utf-8")).hexdigest()
        return f"llm_cache:{hash_digest}"

    def get(self, prompt: str, system_message: str = "", provider: str = "", vision: bool = False) -> Optional[Dict[str, Any]]:
        key = self._generate_key(prompt, system_message, provider, vision)
        cached_val = self.cache.get(key, default=None)
        if cached_val:
            logger.debug(f"LLMCache HIT for key {key[:20]}...")
            try:
                return json.loads(cached_val)
            except Exception:
                return {"text": str(cached_val), "cached": True}
        return None

    def set(self, prompt: str, response_data: Dict[str, Any], system_message: str = "", provider: str = "", vision: bool = False) -> None:
        key = self._generate_key(prompt, system_message, provider, vision)
        try:
            self.cache.set(key, json.dumps(response_data), expire=self.ttl)
            logger.debug(f"LLMCache SET for key {key[:20]}...")
        except Exception as e:
            logger.warning(f"Failed to cache LLM response: {e}")
