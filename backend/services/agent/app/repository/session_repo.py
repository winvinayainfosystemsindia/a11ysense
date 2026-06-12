"""
AuditSessionRepo — PostgreSQL-backed repository for live audit sessions and violations.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from common.database.connection import get_session_local
from common.database.models import AuditSession, Organization, Project, ViolationRecord, AuditProgress

logger = logging.getLogger(__name__)


class AuditSessionRepo:
    """Repository class encapsulating queries and commits for AuditSession and ViolationRecord models."""

    def bootstrap_session(
        self,
        task_id: str,
        url: str,
        org_id: Optional[str] = None,
        proj_id: Optional[str] = None
    ) -> AuditSession:
        """Create a new AuditSession record with tenant resolution."""
        db = get_session_local()()
        try:
            resolved_org_id = None
            if org_id:
                try:
                    resolved_org_id = uuid.UUID(org_id)
                except ValueError:
                    logger.warning(f"Invalid org_id UUID: {org_id}")
            
            if not resolved_org_id:
                first_org = db.query(Organization).first()
                if first_org:
                    resolved_org_id = first_org.id

            resolved_proj_id = None
            if proj_id:
                try:
                    resolved_proj_id = uuid.UUID(proj_id)
                except ValueError:
                    logger.warning(f"Invalid proj_id UUID: {proj_id}")
            
            if not resolved_proj_id and resolved_org_id:
                default_proj = db.query(Project).filter_by(
                    name="Default Project",
                    organization_id=resolved_org_id
                ).first()
                if default_proj:
                    resolved_proj_id = default_proj.id

            session_record = AuditSession(
                task_id=task_id,
                url=url,
                status="crawling",
                organization_id=resolved_org_id,
                project_id=resolved_proj_id,
                timestamp=datetime.utcnow()
            )
            db.add(session_record)
            db.commit()
            db.refresh(session_record)
            return session_record
        except Exception as e:
            db.rollback()
            logger.error(f"[AuditSessionRepo] Failed to bootstrap session for {task_id}: {e}")
            raise
        finally:
            db.close()

    def get_session_by_task_id(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve AuditSession record details by task_id as a dictionary to avoid lazy loading/context issues."""
        db = get_session_local()()
        try:
            session_rec = db.query(AuditSession).filter_by(task_id=task_id).first()
            if session_rec:
                return {
                    "id": session_rec.id,
                    "task_id": session_rec.task_id,
                    "url": session_rec.url,
                    "status": session_rec.status,
                    "timestamp": session_rec.timestamp,
                    "summary": session_rec.summary,
                    "organization_id": session_rec.organization_id,
                    "project_id": session_rec.project_id
                }
            return None
        except Exception as e:
            logger.error(f"[AuditSessionRepo] get_session_by_task_id failed for {task_id}: {e}")
            return None
        finally:
            db.close()

    def update_session_status(self, task_id: str, status: str) -> bool:
        """Update the status of an AuditSession."""
        db = get_session_local()()
        try:
            session_rec = db.query(AuditSession).filter_by(task_id=task_id).first()
            if session_rec:
                session_rec.status = status
                db.commit()
                return True
            return False
        except Exception as e:
            db.rollback()
            logger.error(f"[AuditSessionRepo] Failed to update session status to {status} for {task_id}: {e}")
            raise
        finally:
            db.close()

    def save_session_results(
        self,
        task_id: str,
        status: str,
        summary_data: Dict[str, Any],
        violations: List[Any]
    ) -> bool:
        """Persist full AuditSession summary and individual ViolationRecord rows."""
        db = get_session_local()()
        try:
            session_rec = db.query(AuditSession).filter_by(task_id=task_id).first()
            if session_rec:
                session_rec.status = status
                session_rec.summary = summary_data
                
                # Delete existing violations for this session
                db.query(ViolationRecord).filter_by(audit_session_id=session_rec.id).delete()
                
                # Insert new violation records
                for v in violations:
                    violation_rec = ViolationRecord(
                        audit_session_id=session_rec.id,
                        rule_id=v.id,
                        impact=v.impact,
                        description=v.description,
                        help=v.help,
                        help_url=getattr(v, 'helpUrl', getattr(v, 'help_url', None)),
                        nodes=v.nodes,
                        metadata_json=v.metadata
                    )
                    db.add(violation_rec)
                
                db.commit()
                return True
            return False
        except Exception as e:
            db.rollback()
            logger.error(f"[AuditSessionRepo] Failed to save session results for {task_id}: {e}")
            raise
        finally:
            db.close()

    def mark_session_failed(self, task_id: str, error: str, token_usage: Dict[str, Any]) -> bool:
        """Mark an AuditSession as failed with error details."""
        db = get_session_local()()
        try:
            session_rec = db.query(AuditSession).filter_by(task_id=task_id).first()
            if session_rec:
                session_rec.status = "failed"
                session_rec.summary = {
                    "error": error,
                    "accessibility_score": 0.0,
                    "total_violations": 0,
                    "passes_count": 0,
                    "token_usage": token_usage
                }
                db.commit()
                return True
            return False
        except Exception as e:
            db.rollback()
            logger.error(f"[AuditSessionRepo] Failed to mark session failed for {task_id}: {e}")
            raise
        finally:
            db.close()

    def cleanup_stale_tasks(self, cutoff_hours: int = 2) -> tuple[int, int]:
        """Mark tasks stuck in active states for more than cutoff_hours as failed on startup."""
        db = get_session_local()()
        try:
            cutoff = datetime.utcnow() - timedelta(hours=cutoff_hours)
            stale_sessions = db.query(AuditSession).filter(
                AuditSession.status.in_(["crawling", "auditing"]),
                AuditSession.timestamp < cutoff
            ).all()
            stale_progress = db.query(AuditProgress).filter(
                AuditProgress.status.in_(["crawling", "auditing", "processing"]),
                AuditProgress.created_at < cutoff
            ).all()

            for s in stale_sessions:
                s.status = "failed"
                s.summary = {
                    "error": "Task timed out (stale state cleanup on restart)",
                    "accessibility_score": 0.0,
                    "total_violations": 0,
                    "passes_count": 0,
                    "token_usage": {}
                }
            
            for p in stale_progress:
                p.status = "failed"
                p.error = "Task timed out (stale state cleanup on restart)"

            session_count = len(stale_sessions)
            progress_count = len(stale_progress)

            if session_count > 0 or progress_count > 0:
                db.commit()

            return session_count, progress_count
        except Exception as e:
            db.rollback()
            logger.error(f"[AuditSessionRepo] Startup cleanup failed: {e}")
            raise
        finally:
            db.close()

    def get_telemetry_data(self) -> Dict[str, Any]:
        """Gather database-level counts and totals for dashboard/metrics reporting."""
        db = get_session_local()()
        try:
            active_count = db.query(AuditSession).filter(
                AuditSession.status.in_(["crawling", "auditing"])
            ).count()
            total_count = db.query(AuditSession).count()
            completed_count = db.query(AuditSession).filter(AuditSession.status == "completed").count()
            failed_count = db.query(AuditSession).filter(AuditSession.status == "failed").count()

            active_progress_rows = db.query(AuditProgress).filter(
                AuditProgress.status.in_(["crawling", "auditing", "processing"])
            ).all()

            active_tasks = []
            for row in active_progress_rows:
                active_tasks.append({
                    "task_id": row.task_id,
                    "status": row.status,
                    "url": row.url,
                    "pages_completed": row.pages_completed or 0,
                    "pages_total": row.pages_total or 0,
                    "created_at": row.created_at.isoformat() if row.created_at else None
                })

            total_input_tokens = 0
            total_output_tokens = 0
            total_tokens = 0
            total_violations = 0

            sessions = db.query(AuditSession).filter(AuditSession.summary.isnot(None)).all()
            for s in sessions:
                summary = s.summary or {}
                tok = summary.get("token_usage", {})
                total_input_tokens += tok.get("tokens_sent", 0) or tok.get("tokens_input", 0)
                total_output_tokens += tok.get("tokens_received", 0) or tok.get("tokens_output", 0)
                total_tokens += tok.get("tokens_total", 0) or (
                    tok.get("tokens_sent", 0) + tok.get("tokens_received", 0)
                )
                total_violations += summary.get("total_violations", 0)

            return {
                "active_count": active_count,
                "total_count": total_count,
                "completed_count": completed_count,
                "failed_count": failed_count,
                "active_tasks": active_tasks,
                "total_input_tokens": total_input_tokens,
                "total_output_tokens": total_output_tokens,
                "total_tokens": total_tokens,
                "total_violations_found": total_violations
            }
        except Exception as e:
            logger.error(f"[AuditSessionRepo] Failed to fetch telemetry data: {e}")
            raise
        finally:
            db.close()


# Global singleton instance
audit_session_repo = AuditSessionRepo()
