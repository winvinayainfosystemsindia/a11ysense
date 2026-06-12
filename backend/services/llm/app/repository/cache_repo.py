import json
import hashlib
import logging
import os
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Redis Connection Cache
_redis_client = None
# Local In-Memory Fallback Cache
_memory_cache: Dict[str, str] = {}

class CacheRepository:
    def get_redis_client(self):
        """
        Acquires a persistent connection to the Redis client.
        """
        global _redis_client
        if _redis_client is not None:
            return _redis_client if _redis_client is not False else None
            
        try:
            import redis
            redis_host = os.getenv("REDIS_HOST", "localhost")
            client = redis.Redis(host=redis_host, port=6379, db=0, socket_timeout=2.0)
            client.ping()
            _redis_client = client
            logger.info("Successfully connected to Redis cache backend.")
        except Exception as e:
            logger.warning(f"Redis is not available, falling back to In-Memory local cache. Detail: {str(e)}")
            _redis_client = False
            
        return _redis_client if _redis_client is not False else None

    def generate_cache_key(self, prompt: str, system_message: str) -> str:
        """
        Generates a unique SHA-256 hash for a prompt-system configuration.
        """
        combined = f"system:{system_message}|prompt:{prompt}"
        return hashlib.sha256(combined.encode("utf-8")).hexdigest()

    def get_cached_completion(self, prompt: str, system_message: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a cached LLM completion response. Returns None on cache miss.
        """
        key = self.generate_cache_key(prompt, system_message)
        client = self.get_redis_client()
        
        if client:
            try:
                cached_val = client.get(f"llm:cache:{key}")
                if cached_val:
                    logger.info("Cache Hit via Redis.")
                    return json.loads(cached_val)
            except Exception as e:
                logger.error(f"Error querying Redis cache: {str(e)}")
        else:
            # Memory Fallback
            if key in _memory_cache:
                logger.info("Cache Hit via In-Memory fallback.")
                return json.loads(_memory_cache[key])
                
        return None

    def set_cached_completion(self, prompt: str, system_message: str, response_data: Dict[str, Any]) -> None:
        """
        Stores an LLM completion response inside the cache.
        Response data is serialized to JSON string.
        """
        key = self.generate_cache_key(prompt, system_message)
        client = self.get_redis_client()
        serialized = json.dumps(response_data)
        
        if client:
            try:
                # Cache for 24 hours (86400 seconds)
                client.setex(f"llm:cache:{key}", 86400, serialized)
            except Exception as e:
                logger.error(f"Error writing to Redis cache: {str(e)}")
        else:
            # Memory Fallback
            _memory_cache[key] = serialized

cache_repo = CacheRepository()
