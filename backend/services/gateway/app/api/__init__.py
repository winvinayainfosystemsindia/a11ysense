"""
Gateway API sub-routers package.
Each module owns a single responsibility area.
"""
from app.api.auth import router as auth_router
from app.api.projects import router as projects_router
from app.api.keys import router as keys_router
from app.api.dashboard import router as dashboard_router
from app.api.admin import router as admin_router
from app.api.proxy import router as proxy_router
from app.api.billing import router as billing_router

__all__ = [
    "auth_router",
    "projects_router",
    "keys_router",
    "dashboard_router",
    "admin_router",
    "proxy_router",
    "billing_router",
]
