"""
Cross-platform DiskCache module replacing Redis.
Works seamlessly on Windows, Linux, and macOS without requiring Redis server.
"""
import os
import diskcache
from pathlib import Path

# Cache storage directory
CACHE_DIR = os.getenv("DISKCACHE_DIR", str(Path(__file__).parent.parent / "storage" / "diskcache"))
os.makedirs(CACHE_DIR, exist_ok=True)

# Shared cache instance
cache = diskcache.Cache(CACHE_DIR)

def get_cache() -> diskcache.Cache:
    """Get the global diskcache instance."""
    return cache

def set_cache_val(key: str, value: str, expire: int = None):
    """Set key with optional expiration in seconds."""
    cache.set(key, value, expire=expire)

def get_cache_val(key: str) -> str:
    """Get string value by key."""
    return cache.get(key, default=None)

def delete_cache_val(key: str):
    """Delete a key from cache."""
    cache.delete(key)
