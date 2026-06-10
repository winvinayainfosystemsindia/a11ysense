"""
DEPRECATED — in-memory task store removed.

All task state is now persisted in PostgreSQL via AuditProgressRepo.
Import from app.repository.audit_repo instead:

    from app.repository.audit_repo import audit_progress_repo
"""

# This dict is intentionally empty and no longer used.
# Kept only to prevent ImportError in case any transient reference remains.
from typing import Dict, Any
ACTIVE_TASKS: Dict[str, Any] = {}
