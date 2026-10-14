import uuid
import re
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from common.database.models import Defect, DefectEvent

logger = logging.getLogger(__name__)


class DefectRepository:
    def get_defects_by_project(
        self,
        db: Session,
        project_id: str,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[Defect], int]:
        p_uuid = uuid.UUID(project_id) if isinstance(project_id, str) else project_id
        query = db.query(Defect).filter(Defect.project_id == p_uuid)
        if status:
            query = query.filter(Defect.status == status)
        if severity:
            query = query.filter(Defect.severity == severity)

        total = query.count()
        defects = query.order_by(Defect.defect_code.asc()).offset(offset).limit(limit).all()
        return defects, total

    def get_defect_by_id(self, db: Session, defect_id: str) -> Optional[Defect]:
        try:
            d_uuid = uuid.UUID(defect_id) if isinstance(defect_id, str) else defect_id
            found = db.query(Defect).filter(Defect.id == d_uuid).first()
            if found:
                return found
        except (ValueError, TypeError):
            pass
        return db.query(Defect).filter(Defect.defect_code == defect_id).first()

    def get_defect_by_fingerprint(self, db: Session, project_id: str, fingerprint: str) -> Optional[Defect]:
        p_uuid = uuid.UUID(project_id) if isinstance(project_id, str) else project_id
        return (
            db.query(Defect)
            .filter(Defect.project_id == p_uuid, Defect.fingerprint == fingerprint)
            .first()
        )

    def get_project_defects_map(self, db: Session, project_id: str) -> Dict[str, Defect]:
        """Returns all defects for the project mapped by exact fingerprint."""
        p_uuid = uuid.UUID(project_id) if isinstance(project_id, str) else project_id
        defects = db.query(Defect).filter(Defect.project_id == p_uuid).all()
        return {d.fingerprint: d for d in defects}

    def get_unmatched_defects(
        self,
        db: Session,
        project_id: str,
        matched_defect_ids: Optional[set] = None
    ) -> List[Defect]:
        """Returns defects for the project that haven't been matched yet."""
        p_uuid = uuid.UUID(project_id) if isinstance(project_id, str) else project_id
        matched = matched_defect_ids or set()
        query = db.query(Defect).filter(Defect.project_id == p_uuid)
        if matched:
            query = query.filter(~Defect.id.in_(matched))
        return query.all()

    def get_next_defect_code(self, db: Session, project_id: str) -> str:
        p_uuid = uuid.UUID(project_id) if isinstance(project_id, str) else project_id
        all_codes = db.query(Defect.defect_code).filter(Defect.project_id == p_uuid).all()
        max_num = 0
        for (code,) in all_codes:
            if code and code.startswith("DEF-"):
                try:
                    num = int(code.split("-")[1])
                    if num > max_num:
                        max_num = num
                except (ValueError, IndexError):
                    pass
        return f"DEF-{max_num + 1:04d}"

    def create_defect(self, db: Session, defect_data: Dict[str, Any]) -> Defect:
        defect = Defect(**defect_data)
        db.add(defect)
        db.flush()
        return defect

    def update_defect(self, db: Session, defect_id: str, updates: Dict[str, Any]) -> Optional[Defect]:
        defect = self.get_defect_by_id(db, defect_id)
        if not defect:
            return None
        for k, v in updates.items():
            if hasattr(defect, k):
                setattr(defect, k, v)
        defect.updated_at = datetime.utcnow()
        db.flush()
        return defect

    def add_defect_event(
        self,
        db: Session,
        defect_id: uuid.UUID,
        event: str,
        audit_session_id: Optional[uuid.UUID] = None,
        user_id: Optional[uuid.UUID] = None,
        from_status: Optional[str] = None,
        to_status: Optional[str] = None,
        note: Optional[str] = None
    ) -> DefectEvent:
        evt = DefectEvent(
            defect_id=defect_id,
            audit_session_id=audit_session_id,
            user_id=user_id,
            event=event,
            from_status=from_status,
            to_status=to_status,
            note=note
        )
        db.add(evt)
        db.flush()
        return evt

    def get_defect_timeline(self, db: Session, defect_id: str) -> List[DefectEvent]:
        try:
            d_uuid = uuid.UUID(defect_id) if isinstance(defect_id, str) else defect_id
            return (
                db.query(DefectEvent)
                .filter(DefectEvent.defect_id == d_uuid)
                .order_by(DefectEvent.created_at.asc())
                .all()
            )
        except (ValueError, TypeError):
            return []


defect_repo = DefectRepository()
