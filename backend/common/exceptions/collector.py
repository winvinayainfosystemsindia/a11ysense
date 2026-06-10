import os
import json
import logging
import threading
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)


def log_error_event(event: Dict[str, Any]) -> None:
    """
    Persists an incoming error event object into the central PostgreSQL error_events table.
    """
    try:
        from common.database.connection import get_session_local
        from common.database.models import ErrorEventRecord

        db_session = get_session_local()()
        try:
            timestamp_str = event.get("timestamp")
            if timestamp_str:
                try:
                    # Parse ISO format, handling 'Z' suffix safely
                    ts = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                except Exception:
                    ts = datetime.utcnow()
            else:
                ts = datetime.utcnow()

            db_event = ErrorEventRecord(
                correlation_id=event.get("correlation_id"),
                service_name=event.get("service_name"),
                severity=event.get("severity", "error"),
                message=event.get("message"),
                timestamp=ts,
                context_json=event.get("context", {})
            )
            db_session.add(db_event)
            db_session.commit()
        except Exception as pg_err:
            logger.warning(f"Failed to log error event in PostgreSQL: {str(pg_err)}")
            db_session.rollback()
        finally:
            db_session.close()
    except Exception as import_err:
        logger.warning(f"Database module unavailable for telemetry logging: {str(import_err)}")


class ErrorCollector:
    """
    Background subscriber worker listening to the Redis errors channel
    and executing stateful PostgreSQL logging and alerting thresholds.
    """
    def __init__(self):
        self.redis_host = os.getenv("REDIS_HOST", "localhost")
        self._running = False
        self._thread = None

    def start(self) -> None:
        """
        Launches the subscriber loop inside a dedicated background worker thread.
        """
        self._running = True
        self._thread = threading.Thread(target=self._run_collector_thread, daemon=True)
        self._thread.start()
        logger.info("ErrorCollector: Background worker thread spawned successfully.")

    def stop(self) -> None:
        """
        Gracefully terminates the background collector worker.
        """
        self._running = False
        logger.info("ErrorCollector: Shutting down background worker thread.")

    def _run_collector_thread(self) -> None:
        """
        Standard blocking loop executing Redis Pub/Sub reads on the background thread.
        Uses exponential backoff (5s → 60s cap) when Redis is unavailable.
        """
        import redis
        import time
        from common.exceptions.alerting import evaluate_alert_rules

        retry_delay = 5.0
        max_delay = 60.0

        while self._running:
            try:
                client = redis.Redis(host=self.redis_host, port=6379, db=0, socket_timeout=5.0)
                # Ping to verify connection before subscribing
                client.ping()
                pubsub = client.pubsub(ignore_subscribe_messages=True)
                pubsub.subscribe("errors:event_bus")

                logger.info("ErrorCollector: Successfully subscribed to errors:event_bus channel.")
                # Reset backoff on successful connection
                retry_delay = 5.0

                while self._running:
                    # Blocking poll with a short timeout
                    message = pubsub.get_message(timeout=1.0)
                    if message and message.get("type") == "message":
                        try:
                            raw_data = message.get("data")
                            if raw_data:
                                event = json.loads(raw_data.decode("utf-8"))

                                # 1. Log to PostgreSQL
                                log_error_event(event)

                                # 2. Trigger real-time alert evaluation rules
                                evaluate_alert_rules(event)
                        except Exception as parse_err:
                            logger.error(f"ErrorCollector: Failed to process error message: {str(parse_err)}")

            except Exception as conn_err:
                logger.warning(
                    f"ErrorCollector: Redis event bus unavailable. "
                    f"Retrying in {retry_delay:.0f}s... Detail: {str(conn_err)}"
                )
                time.sleep(retry_delay)
                # Double the delay up to the cap
                retry_delay = min(retry_delay * 2, max_delay)


# Global persistent singleton instance
error_collector = ErrorCollector()
