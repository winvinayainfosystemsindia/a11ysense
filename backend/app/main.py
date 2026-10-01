"""
A11ySense AI — Unified Monolith Backend Application
Single high-performance FastAPI service replacing microservices architecture.
"""
import sys
import os
import asyncio

# Set ProactorEventLoop on Windows for Playwright asyncio subprocess support
if sys.platform == "win32":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except Exception:
        pass

# Add root and backend to python path for module resolution
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import logging
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from common.database.connection import get_engine
from common.database.init_db import init_db
from backend.app.cache import get_cache

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("a11ysense.monolith")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown hooks."""
    logger.info("Initializing A11ySense AI Monolith Backend...")
    # Initialize DB schema & seed default data
    init_db()
    # Initialize DiskCache
    get_cache()
    logger.info("Monolith Backend successfully started.")
    yield
    logger.info("Shutting down A11ySense AI Monolith Backend...")

app = FastAPI(
    title="A11ySense AI Monolith API",
    description="Unified Production-Ready Accessibility Testing Monolith",
    version="2.0.0",
    lifespan=lifespan
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Storage directories
STORAGE_DIR = os.getenv("STORAGE_DIR", "storage")
REPORTS_DIR = os.path.join(STORAGE_DIR, "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

app.mount("/static/reports", StaticFiles(directory=REPORTS_DIR), name="reports")

@app.get("/health", tags=["Health"])
@app.get("/v1/health", tags=["Health"])
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "service": "a11ysense-monolith", "version": "2.0.0"}

@app.get("/metrics", tags=["Metrics"])
@app.get("/v1/metrics", tags=["Metrics"])
async def metrics_stub():
    """Legacy metrics stub endpoint."""
    return {"status": "ok"}

from fastapi.responses import StreamingResponse
import json
import asyncio

@app.get("/v1/agents/telemetry/stream", tags=["Telemetry"])
@app.get("/agents/telemetry/stream", tags=["Telemetry"])
async def telemetry_stream_stub(token: Optional[str] = None):
    """Server-Sent Events telemetry stream stub."""
    async def _event_generator():
        yield f"data: {json.dumps({'event': 'ping', 'status': 'connected', 'message': 'Connected to live telemetry gateway.'})}\n\n"
        while True:
            await asyncio.sleep(15)
            yield f"data: {json.dumps({'event': 'ping', 'status': 'alive', 'message': 'Telemetry stream heartbeat.'})}\n\n"

    return StreamingResponse(
        _event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

# Register API Routers
from backend.app.api.auth import router as auth_router
from backend.app.api.projects import router as projects_router
from backend.app.api.credentials import router as credentials_router
from backend.app.api.audit import router as audit_router
from backend.app.api.reports import router as reports_router
from backend.app.api.dashboard import router as dashboard_router
from backend.app.api.users import router as users_router

# Root prefixed routes (/auth, /api/projects, etc.)
app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(credentials_router)
app.include_router(audit_router)
app.include_router(reports_router)
app.include_router(dashboard_router)
app.include_router(users_router)

# /v1 prefixed routes (/v1/auth, /v1/api/projects, etc.)
app.include_router(auth_router, prefix="/v1")
app.include_router(projects_router, prefix="/v1")
app.include_router(credentials_router, prefix="/v1")
app.include_router(audit_router, prefix="/v1")
app.include_router(reports_router, prefix="/v1")
app.include_router(dashboard_router, prefix="/v1")
app.include_router(users_router, prefix="/v1")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=port, reload=True)
