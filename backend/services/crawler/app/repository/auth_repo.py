import json
import logging
from typing import Optional
from common.utils.event_bus import get_redis_client

logger = logging.getLogger(__name__)

SESSION_TTL_SECONDS = 30 * 60  # 30 minutes TTL

class AuthRepository:
    def get_redis_key(self, task_id: str) -> str:
        return f"auth:session:{task_id}"

    def save_session_state(self, task_id: str, state_json: str) -> bool:
        client = get_redis_client()
        if not client:
            logger.warning("Redis client not available, unable to save session state.")
            return False
        try:
            key = self.get_redis_key(task_id)
            client.setex(key, SESSION_TTL_SECONDS, state_json)
            return True
        except Exception as e:
            logger.error(f"Failed to save session state to Redis: {e}")
            return False

    def load_session_state(self, task_id: str) -> Optional[str]:
        client = get_redis_client()
        if not client:
            logger.warning("Redis client not available, unable to load session state.")
            return None
        try:
            key = self.get_redis_key(task_id)
            val = client.get(key)
            return val.decode("utf-8") if val else None
        except Exception as e:
            logger.error(f"Failed to load session state from Redis: {e}")
            return None

    def delete_session_state(self, task_id: str) -> bool:
        client = get_redis_client()
        if not client:
            return False
        try:
            key = self.get_redis_key(task_id)
            client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Failed to delete session state from Redis: {e}")
            return False

auth_repo = AuthRepository()
