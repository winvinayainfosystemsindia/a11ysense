import os
import json
import traceback
import logging
from datetime import datetime
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from common.utils.correlation import get_correlation_id, set_correlation_id
from common.exceptions import A11ySenseBaseException

logger = logging.getLogger(__name__)

# Redis Pub/Sub client setup
_redis_pub_client = None

def get_redis_publisher():
    """
    Acquires a persistent connection to the Redis event bus.
    """
    global _redis_pub_client
    if _redis_pub_client is not None:
        return _redis_pub_client

    try:
        import redis
        redis_host = os.getenv("REDIS_HOST", "localhost")
        _redis_pub_client = redis.Redis(host=redis_host, port=6379, db=0, socket_timeout=2.0)
        _redis_pub_client.ping()
    except Exception as e:
        logger.warning(f"Exception Handler: Redis event bus not available for error streaming. Detail: {str(e)}")
        _redis_pub_client = False
        
    return _redis_pub_client

class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Intercepts incoming requests to extract or inject the X-Correlation-ID tracking header.
    Binds the correlation ID to contextvars.
    """
    async def dispatch(self, request: Request, call_next):
        correlation_id = request.headers.get("X-Correlation-ID") or request.headers.get("x-correlation-id")
        if not correlation_id:
            import uuid
            correlation_id = str(uuid.uuid4())
            
        # Bind context
        set_correlation_id(correlation_id)
        
        response = await call_next(request)
        
        # Inject correlation header in response
        response.headers["X-Correlation-ID"] = correlation_id
        return response

def setup_global_exception_handler(app: FastAPI, service_name: str) -> None:
    """
    Mounts correlation middleware and registers unified exception interceptors
    for standard and uncaught errors across any FastAPI microservice.
    """
    # 1. Mount async-safe correlation tracer middleware
    app.add_middleware(CorrelationIdMiddleware)
    
    # 2. Register Global Exception Handlers
    @app.exception_handler(A11ySenseBaseException)
    async def custom_exception_handler(request: Request, exc: A11ySenseBaseException):
        """
        Intercepts custom system exception failures, logs details, streams to Redis bus,
        and returns clean JSON.
        """
        error_payload = exc.to_dict()
        
        # Add stacktrace details to payload context for developers
        tb = traceback.format_exc()
        if "traceback" not in error_payload["context"] and tb != "NoneType: None\n":
            error_payload["context"]["traceback"] = tb
            
        logger.error(f"[{service_name.upper()}] Exception Intercepted: {exc.message} (CorrelationID={exc.correlation_id})")
        
        # Stream asynchronously to Redis Pub/Sub bus
        _publish_to_redis_bus(service_name, error_payload)
        
        return JSONResponse(
            status_code=500,
            content=error_payload
        )

    @app.exception_handler(StarletteHTTPException)
    async def HTTP_exception_handler(request: Request, exc: StarletteHTTPException):
        """
        Standardizes default FastAPI HTTPExceptions into unified platform exception payload format.
        """
        correlation_id = get_correlation_id()
        error_payload = {
            "error": True,
            "message": exc.detail,
            "service_name": service_name,
            "correlation_id": correlation_id,
            "severity": "error" if exc.status_code >= 500 else "warning",
            "timestamp": datetime.utcnow().isoformat(),
            "context": {"status_code": exc.status_code}
        }
        
        logger.warning(f"[{service_name.upper()}] HTTP Exception Intercepted: {exc.detail} (Status={exc.status_code})")
        _publish_to_redis_bus(service_name, error_payload)
        
        return JSONResponse(
            status_code=exc.status_code,
            content=error_payload
        )

    @app.exception_handler(Exception)
    async def uncaught_exception_handler(request: Request, exc: Exception):
        """
        Intercepts uncaught Python raw tracebacks, maps them as CRITICAL severity,
        streams telemetry details to Redis, and returns standard clean error schema.
        """
        correlation_id = get_correlation_id()
        tb = traceback.format_exc()
        
        error_payload = {
            "error": True,
            "message": str(exc),
            "service_name": service_name,
            "correlation_id": correlation_id,
            "severity": "critical",
            "timestamp": datetime.utcnow().isoformat(),
            "context": {
                "exception_type": exc.__class__.__name__,
                "traceback": tb
            }
        }
        
        logger.critical(f"[{service_name.upper()}] UNCAUGHT CRITICAL CRASH: {str(exc)}\n{tb}", exc_info=True)
        
        # Publish event
        _publish_to_redis_bus(service_name, error_payload)
        
        return JSONResponse(
            status_code=500,
            content={
                "error": True,
                "message": "An unexpected server error occurred. Please contact system support.",
                "service_name": service_name,
                "correlation_id": correlation_id,
                "severity": "critical",
                "timestamp": error_payload["timestamp"]
            }
        )

def _publish_to_redis_bus(service_name: str, payload: dict) -> None:
    """
    Non-blocking event dispatcher publishing serialized error objects to Redis channel errors:event_bus.
    """
    publisher = get_redis_publisher()
    if not publisher:
        return
        
    try:
        serialized = json.dumps(payload)
        # Publish to unified error collector channel
        publisher.publish("errors:event_bus", serialized)
    except Exception as e:
        logger.warning(f"Exception Handler: Failed to publish exception event to Redis: {str(e)}")
