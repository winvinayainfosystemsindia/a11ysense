"""
Admin Router — centralized error/fault tracing dashboard (Admin-only)
  GET /admin/errors              — serves the HTML fault tracing UI
  GET /api/admin/errors/stats    — returns JSON error stats from PostgreSQL
"""
import json
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from common.database import get_db
from common.database.models import User, ErrorEventRecord
from common.auth.deps import require_role
from app.utils.dashboard import get_admin_dashboard_html

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
    try:
        # 1. Total errors
        total_errors = db.query(ErrorEventRecord).count()

        # 2. Critical count
        critical_count = db.query(ErrorEventRecord).filter_by(severity="critical").count()

        # 3. Standard error count
        error_count = db.query(ErrorEventRecord).filter_by(severity="error").count()

        # 4. Breakdown by service
        breakdown_rows = (
            db.query(ErrorEventRecord.service_name, func.count(ErrorEventRecord.id))
            .group_by(ErrorEventRecord.service_name)
            .all()
        )
        service_breakdown = {row[0]: row[1] for row in breakdown_rows}

        # 5. Latest 50 logs ordered newest-first (created_at desc)
        logs = (
            db.query(ErrorEventRecord)
            .order_by(ErrorEventRecord.created_at.desc())
            .limit(50)
            .all()
        )

        latest_logs = []
        for log in logs:
            # Safely serialize context to a JSON string to match the JavaScript dashboard's JSON.parse requirement
            context_str = "{}"
            if log.context_json:
                if isinstance(log.context_json, dict) or isinstance(log.context_json, list):
                    context_str = json.dumps(log.context_json)
                else:
                    context_str = str(log.context_json)

            latest_logs.append({
                "id": str(log.id),
                "correlation_id": log.correlation_id or "N/A",
                "service_name": log.service_name,
                "severity": log.severity,
                "message": log.message,
                "timestamp": log.timestamp.isoformat() if log.timestamp else datetime.utcnow().isoformat(),
                "context_json": context_str
            })

        return {
            "total_errors": total_errors,
            "critical_count": critical_count,
            "error_count": error_count,
            "service_breakdown": service_breakdown,
            "latest_logs": latest_logs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database Query Failure: {str(e)}")
