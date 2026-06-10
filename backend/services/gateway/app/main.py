"""
A11ySense AI — Gateway Service Entry Point

Responsibilities of this file (only):
  - App instantiation
  - Middleware registration
  - Startup / shutdown lifecycle hooks
  - Sub-router registration

All business logic lives in app/api/*.py
"""
import asyncio
import sys

# Windows event loop policy patch (must precede any asyncio use)
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from common.config import setup_environment, get_cors_origins
setup_environment()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from common.database import init_db
from common.exceptions.collector import error_collector
from common.exceptions.handler import setup_global_exception_handler

from app.api import (
    auth_router,
    projects_router,
    keys_router,
    dashboard_router,
    admin_router,
    proxy_router,
    billing_router,
    users_router,
)

# ── Versioning ─────────────────────────────────────────────────────────────
#
# All public API routes are served under /v1.
# To introduce a breaking change in future: create app/api/v2/*.py routers
# and include them here with prefix="/v2" alongside the existing /v1 routers.

API_VERSION = "v1"
API_PREFIX = f"/{API_VERSION}"

# ── App ────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="A11ySense AI Gateway",
    description=(
        "Central API gateway — authentication, RBAC, project management, and audit proxy.\n\n"
        f"**Current API version:** `{API_VERSION}`  \n"
        f"All routes are prefixed with `{API_PREFIX}`."
    ),
    version="1.0.0",
    docs_url=f"{API_PREFIX}/docs",
    redoc_url=f"{API_PREFIX}/redoc",
    openapi_url=f"{API_PREFIX}/openapi.json",
)

# ── Exception handler ──────────────────────────────────────────────────────

setup_global_exception_handler(app, "gateway-service")

# ── Telemetry & Metrics ────────────────────────────────────────────────────

from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app)


# ── CORS ───────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Lifecycle ──────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    """Bootstrap the Redis error collector and PostgreSQL schema on first run."""
    error_collector.start()
    try:
        init_db()
    except Exception as e:
        print(f"[Gateway] Failed to bootstrap database on startup: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Gracefully stop the error collector background thread."""
    error_collector.stop()

# ── Version root ───────────────────────────────────────────────────────────

@app.get(API_PREFIX, tags=["Meta"], include_in_schema=False)
async def api_version_root():
    """Returns the active API version and available route groups."""
    return {
        "api": "A11ySense AI Gateway",
        "version": API_VERSION,
        "status": "operational",
        "routes": {
            "auth":      f"{API_PREFIX}/auth",
            "projects":  f"{API_PREFIX}/api/projects",
            "keys":      f"{API_PREFIX}/api/keys",
            "dashboard": f"{API_PREFIX}/api/dashboard/stats",
            "trends":    f"{API_PREFIX}/api/trends",
            "admin":     f"{API_PREFIX}/admin/errors",
            "audit":     f"{API_PREFIX}/start_audit",
            "docs":      f"{API_PREFIX}/docs",
        }
    }

# ── Routers (all mounted under /v1) ───────────────────────────────────────

app.include_router(auth_router,      prefix=API_PREFIX)  # /v1/auth/*
app.include_router(projects_router,  prefix=API_PREFIX)  # /v1/api/projects
app.include_router(keys_router,      prefix=API_PREFIX)  # /v1/api/keys
app.include_router(dashboard_router, prefix=API_PREFIX)  # /v1/api/dashboard/stats  /v1/api/trends
app.include_router(admin_router,     prefix=API_PREFIX)  # /v1/admin/errors  /v1/api/admin/errors/stats
app.include_router(proxy_router,     prefix=API_PREFIX)  # /v1/start_audit  /v1/task/{id}/*
app.include_router(billing_router,   prefix=API_PREFIX)  # /v1/api/billing/*
app.include_router(users_router,     prefix=API_PREFIX)  # /v1/api/users
