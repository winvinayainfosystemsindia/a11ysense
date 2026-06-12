"""
A11ySense AI — Agent Service Entrypoint

Starts the FastAPI server, initializes middleware, registers routers,
and executes startup/cleanup background worker tasks.
"""
import sys
import logging
import asyncio

# Windows event loop policy patch
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from common.config import setup_environment, get_cors_origins
setup_environment()

logger = logging.getLogger(__name__)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.routes import router as api_router
from common.exceptions.handler import setup_global_exception_handler

app = FastAPI(title="OpenClaw Agent Service")

# Setup global exception handler
setup_global_exception_handler(app, "agent-service")

# Instrument the app middleware (latency, status codes, etc.)
Instrumentator().instrument(app)

# CORS middleware config
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the refactored endpoints
app.include_router(api_router)


@app.on_event("startup")
async def startup_event() -> None:
    """Start background Agent Stream listener thread and clean up stale tasks on service launch."""
    # Clean up tasks stuck in active states from previous runs (older than 2 hours)
    try:
        from app.repository.session_repo import audit_session_repo
        session_count, progress_count = audit_session_repo.cleanup_stale_tasks()
        if session_count > 0 or progress_count > 0:
            logger.info(
                f"Startup cleanup: marked {session_count} sessions and "
                f"{progress_count} progress rows as failed."
            )
    except Exception as cleanup_err:
        logger.warning(f"Startup stale task cleanup failed: {cleanup_err}")
    
    # Start the Redis stream polling background thread
    try:
        from app.services.worker import start_agent_audit_worker
        start_agent_audit_worker()
    except Exception as worker_err:
        logger.error(f"Failed to start agent audit worker: {worker_err}")
    
    # Start file cleanup worker
    try:
        from common.utils.storage_cleanup import start_storage_cleanup_worker
        start_storage_cleanup_worker()
    except Exception as cleanup_err:
        logger.warning(f"Failed to start storage cleanup worker: {cleanup_err}")
