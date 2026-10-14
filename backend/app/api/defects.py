import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from common.database.connection import get_db
from common.database.models import User, Defect
from common.auth.deps import get_current_user
from app.repository.defect_repo import defect_repo

router = APIRouter(prefix="/api/defects", tags=["Defects"])


class DefectUpdateSchema(BaseModel):
    status: Optional[str] = None  # WontFix, FalsePositive, Open, Closed
    notes: Optional[str] = None
    suppressed_reason: Optional[str] = None
    assignee_user_id: Optional[str] = None


@router.get("/{defect_id}")
async def get_defect_detail(
    defect_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve full defect detail with latest evidence and historical event timeline."""
    defect = defect_repo.get_defect_by_id(db, defect_id)
    if not defect:
        raise HTTPException(status_code=404, detail="Defect not found")

    events = defect_repo.get_defect_timeline(db, str(defect.id))
    timeline = []
    for ev in events:
        timeline.append({
            "id": str(ev.id),
            "event": ev.event,
            "from_status": ev.from_status,
            "to_status": ev.to_status,
            "note": ev.note,
            "audit_session_id": str(ev.audit_session_id) if ev.audit_session_id else None,
            "run_number": ev.session.run_number if ev.session else None,
            "user_email": ev.user.email if ev.user else None,
            "created_at": ev.created_at.isoformat() if ev.created_at else None
        })

    age_days = (datetime.utcnow() - defect.created_at).days if defect.created_at else 0

    return {
        "id": str(defect.id),
        "project_id": str(defect.project_id),
        "defect_code": defect.defect_code,
        "title": defect.title,
        "rule_id": defect.rule_id,
        "page_url": defect.page_url,
        "severity": defect.severity,
        "status": defect.status,
        "first_seen_run": defect.first_seen_run.run_number if defect.first_seen_run else 1,
        "last_seen_run": defect.last_seen_run.run_number if defect.last_seen_run else None,
        "fixed_in_run": defect.fixed_in_run.run_number if defect.fixed_in_run else None,
        "reopen_count": defect.reopen_count,
        "times_seen": defect.times_seen,
        "age_days": age_days,
        "code_before": defect.code_before,
        "code_after": defect.code_after,
        "fix_steps": defect.fix_steps or [],
        "verify_steps": defect.verify_steps or [],
        "false_positive_note": defect.false_positive_note,
        "notes": defect.notes,
        "suppressed_reason": defect.suppressed_reason,
        "assignee_user_id": str(defect.assignee_user_id) if defect.assignee_user_id else None,
        "created_at": defect.created_at.isoformat() if defect.created_at else None,
        "updated_at": defect.updated_at.isoformat() if defect.updated_at else None,
        "timeline": timeline
    }


@router.patch("/{defect_id}")
async def update_defect(
    defect_id: str,
    payload: DefectUpdateSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update defect status (e.g. Won't Fix, False Positive, Open), notes, or suppression reason.
    Appends an audit trail event.
    """
    defect = defect_repo.get_defect_by_id(db, defect_id)
    if not defect:
        raise HTTPException(status_code=404, detail="Defect not found")

    old_status = defect.status
    updates = {}

    if payload.status and payload.status != old_status:
        allowed = {"New", "Open", "Fixed", "Closed", "WontFix", "FalsePositive"}
        if payload.status not in allowed:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {allowed}")
        updates["status"] = payload.status

    if payload.notes is not None:
        updates["notes"] = payload.notes
    if payload.suppressed_reason is not None:
        updates["suppressed_reason"] = payload.suppressed_reason
    if payload.assignee_user_id is not None:
        try:
            updates["assignee_user_id"] = uuid.UUID(payload.assignee_user_id) if payload.assignee_user_id else None
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid assignee UUID")

    updated_defect = defect_repo.update_defect(db, str(defect.id), updates)

    # Append audit trail event
    event_type = "status_changed" if payload.status and payload.status != old_status else "commented"
    note_text = payload.suppressed_reason or payload.notes or f"Status changed to {payload.status}"
    defect_repo.add_defect_event(
        db=db,
        defect_id=defect.id,
        user_id=current_user.id,
        event=event_type,
        from_status=old_status,
        to_status=payload.status or old_status,
        note=note_text
    )
    db.commit()

    return {
        "status": "updated",
        "id": str(updated_defect.id),
        "defect_code": updated_defect.defect_code,
        "new_status": updated_defect.status
    }
