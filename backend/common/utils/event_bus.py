import os
import json
import redis
import logging
import time
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger(__name__)

_redis_client = None
_last_connect_time = 0.0
_connect_cooldown = 10.0  # Retry connecting at most once every 10 seconds if offline

def get_redis_client():
    """
    Acquires a persistent connection to the Redis client.
    """
    global _redis_client, _last_connect_time
    if _redis_client is not None:
        try:
            _redis_client.ping()
            return _redis_client
        except Exception:
            _redis_client = None

    now = time.time()
    if now - _last_connect_time < _connect_cooldown:
        return None

    _last_connect_time = now
    try:
        redis_host = os.getenv("REDIS_HOST", "localhost")
        # Use a local variable to prevent concurrent threads from returning an unvalidated connection
        client = redis.Redis(host=redis_host, port=6379, db=0, socket_timeout=2.0)
        client.ping()
        _redis_client = client
        logger.info("Event Bus: Successfully connected to Redis.")
        return _redis_client
    except Exception as e:
        logger.warning(f"Event Bus: Redis connection failed. Detail: {str(e)}")
        _redis_client = None
        return None


def publish_event(stream_name: str, payload: Dict[str, Any]) -> Optional[str]:
    """
    Appends a JSON payload to a Redis Stream using XADD.
    Returns the message ID string on success, or None on failure.
    """
    client = get_redis_client()
    if not client:
        logger.error(f"Event Bus: Cannot publish to stream '{stream_name}' — Redis unavailable.")
        return None
    try:
        data = {"payload": json.dumps(payload)}
        msg_id = client.xadd(stream_name, data)
        return msg_id.decode("utf-8") if isinstance(msg_id, bytes) else str(msg_id)
    except Exception as e:
        logger.error(f"Event Bus: Failed to xadd to stream '{stream_name}': {str(e)}")
        return None


def read_events(stream_name: str, last_id: str = "$", block_ms: int = 1000) -> List[Tuple[str, Dict[str, Any]]]:
    """
    Reads from a Redis Stream using XREAD with blocking.
    Returns a list of tuples containing (message_id, parsed_json_payload).
    """
    client = get_redis_client()
    if not client:
        return []
    try:
        streams = {stream_name: last_id}
        events = client.xread(streams, block=block_ms)
        if not events:
            return []
        
        parsed_events = []
        for stream, msgs in events:
            for msg_id, data in msgs:
                msg_id_str = msg_id.decode("utf-8") if isinstance(msg_id, bytes) else str(msg_id)
                raw_payload = data.get(b"payload", b"{}")
                try:
                    payload = json.loads(raw_payload.decode("utf-8"))
                    parsed_events.append((msg_id_str, payload))
                except Exception as parse_err:
                    logger.error(f"Event Bus: Failed to parse payload from message '{msg_id_str}': {str(parse_err)}")
        return parsed_events
    except Exception as e:
        # Don't flood the logs with normal polling warnings
        # logger.warning(f"Event Bus: Polling error on stream '{stream_name}': {str(e)}")
        return []
