"""
Admin Router — centralized error/fault tracing dashboard (Admin-only)
  GET /admin/errors              — serves the HTML fault tracing UI
  GET /api/admin/errors/stats    — returns JSON error stats from PostgreSQL
"""
from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from common.database import get_db
from common.database.models import User
from common.auth.deps import require_role
from app.utils.dashboard import get_admin_dashboard_html
from app.services.admin_service import admin_service

router = APIRouter(tags=["Admin"])


# ── Routes ─────────────────────────────────────────────────────────────────

@router.get("/admin/errors", response_class=HTMLResponse)
async def admin_errors_dashboard(
    current_user: User = Depends(require_role(["Admin"]))
):
    """
    Serves the centralized fault tracing HTML dashboard.
    Restricted to Admin role only.
    """
    return get_admin_dashboard_html()


@router.get("/api/admin/errors/stats")
async def admin_errors_stats(
    current_user: User = Depends(require_role(["Admin"])),
    db: Session = Depends(get_db)
):
    """
    Returns compiled error logging statistics and the latest 50 error
    trace records from the central PostgreSQL error event store.
    Restricted to Admin role only.
    """
    return admin_service.get_admin_errors_stats(db)
