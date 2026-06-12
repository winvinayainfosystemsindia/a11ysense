from typing import Optional, Dict, Any
from app.repository.cache_repo import cache_repo

def get_redis_client():
    """Acquires a persistent connection to the Redis client."""
    return cache_repo.get_redis_client()

def _generate_cache_key(prompt: str, system_message: str) -> str:
    """Generates a unique SHA-256 hash for a prompt-system configuration."""
    return cache_repo.generate_cache_key(prompt, system_message)

def get_cached_completion(prompt: str, system_message: str) -> Optional[Dict[str, Any]]:
    """Retrieves a cached LLM completion response."""
    return cache_repo.get_cached_completion(prompt, system_message)

def set_cached_completion(prompt: str, system_message: str, response_data: Dict[str, Any]) -> None:
    """Stores an LLM completion response inside the cache."""
    cache_repo.set_cached_completion(prompt, system_message, response_data)
