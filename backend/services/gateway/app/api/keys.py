"""
API Keys Router — GET /api/keys, POST /api/keys, DELETE /api/keys/{key_id}
"""
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from common.database import get_db
from common.database.models import User
from common.auth.deps import get_current_user, require_role
from app.schemas.keys import ApiKeyCreate, ApiKeyResponse, ApiKeyCreatedResponse
from app.services.key_service import api_key_service

router = APIRouter(prefix="/api/keys", tags=["API Keys"])


# ── Routes ─────────────────────────────────────────────────────────────────

@router.get("", response_model=List[ApiKeyResponse])
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all API keys belonging to the current user's organization."""
    return api_key_service.list_api_keys(current_user, db)


@router.post("", response_model=ApiKeyCreatedResponse)
async def create_api_key(
    req: ApiKeyCreate,
    current_user: User = Depends(require_role(["Auditor", "Admin"])),
    db: Session = Depends(get_db)
):
    """
    Create a new API key for CI/CD integration.
    The raw key is returned ONLY once — store it securely immediately.
    Requires Auditor or Admin role.
    """
    return api_key_service.create_api_key(req, current_user, db)


@router.delete("/{key_id}")
async def revoke_api_key(
    key_id: str,
    current_user: User = Depends(require_role(["Auditor", "Admin"])),
    db: Session = Depends(get_db)
):
    """Revoke an API key by ID. Only keys belonging to the user's organization can be revoked."""
    return api_key_service.revoke_api_key(key_id, current_user, db)
