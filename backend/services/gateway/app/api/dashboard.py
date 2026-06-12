"""
Dashboard & Trends Router
  GET /api/dashboard/stats  — organization-wide audit statistics
  GET /api/trends           — historical compliance score & violation trend series
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from common.database import get_db
from common.database.models import User
from common.auth.deps import get_current_user
from app.services.dashboard_service import dashboard_service

router = APIRouter(prefix="/api", tags=["Dashboard"])


# ── Routes ─────────────────────────────────────────────────────────────────

@router.get("/audits")
async def list_all_audits(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Return all audit sessions for the organization, ordered by descending timestamp.
    """
    return dashboard_service.list_all_audits(current_user, db)


@router.get("/dashboard/stats")
async def get_dashboard_stats(
    time_range: str = "all",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Compile organization-wide audit statistics:
    total audits, pass/fail counts, average accessibility score,
    violation breakdown by impact level, and the 10 most recent sessions.
    """
    return dashboard_service.get_dashboard_stats(time_range, current_user, db)


@router.get("/trends")
async def get_historical_trends(
    time_range: str = "all",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Return historical trend data points for accessibility score and violation count
    across all completed audits in the organization, ordered chronologically.
    """
    return dashboard_service.get_historical_trends(time_range, current_user, db)
