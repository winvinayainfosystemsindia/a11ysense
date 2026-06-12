"""
A11ySense AI — Crawler Service Entrypoint

Starts the FastAPI server, initializes middleware, registers routers,
and executes startup background worker tasks.
"""
import sys
import logging
import asyncio

# Standard fix for Playwright/asyncio subprocesses on Windows
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from common.config import setup_environment, get_cors_origins
# Initialize environment using shared configuration utility
setup_environment()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.routes import router as crawler_router
from common.exceptions.handler import setup_global_exception_handler

logger = logging.getLogger(__name__)

app = FastAPI(title="A11ySense AI Crawler Service")

# Setup global exception handler
setup_global_exception_handler(app, "crawler-service")

# Instrument the app middleware (latency, status codes, etc.)
Instrumentator().instrument(app).expose(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(crawler_router)


@app.on_event("startup")
async def startup_event() -> None:
    """Start the background Crawler Stream subscriber on application launch."""
    try:
        from app.services.worker import start_crawler_worker
        start_crawler_worker()
    except Exception as e:
        logger.error(f"Failed to start crawler worker: {e}")
