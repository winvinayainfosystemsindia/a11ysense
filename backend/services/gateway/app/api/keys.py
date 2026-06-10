"""
API Keys Router — GET /api/keys, POST /api/keys, DELETE /api/keys/{key_id}
"""
import uuid
import hashlib
from typing import List
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from common.database import get_db
from common.database.models import User, ApiKey
from common.auth.deps import get_current_user, require_role
from app.schemas.keys import ApiKeyCreate, ApiKeyResponse, ApiKeyCreatedResponse

router = APIRouter(prefix="/api/keys", tags=["API Keys"])


# ── Routes ─────────────────────────────────────────────────────────────────

@router.get("", response_model=List[ApiKeyResponse])
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all API keys belonging to the current user's organization."""
    keys = (
        db.query(ApiKey)
        .filter_by(organization_id=current_user.organization_id)
        .order_by(ApiKey.created_at.desc())
        .all()
    )
    return keys


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
    # Generate a cryptographically random key
    raw_key = f"a11y_key_{uuid.uuid4().hex}{uuid.uuid4().hex[:16]}"
    hashed_key = hashlib.sha256(raw_key.encode()).hexdigest()

    expires_at = datetime.utcnow() + timedelta(days=req.expires_in_days)

    new_key = ApiKey(
        key_hash=hashed_key,
        name=req.name,
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        expires_at=expires_at
    )
    db.add(new_key)
    db.commit()
    db.refresh(new_key)

    return ApiKeyCreatedResponse(
        id=str(new_key.id),
        name=new_key.name,
        created_at=new_key.created_at,
        expires_at=new_key.expires_at,
        api_key=raw_key  # Returned ONLY this once
    )


@router.delete("/{key_id}")
async def revoke_api_key(
    key_id: str,
    current_user: User = Depends(require_role(["Auditor", "Admin"])),
    db: Session = Depends(get_db)
):
    """Revoke an API key by ID. Only keys belonging to the user's organization can be revoked."""
    key = db.query(ApiKey).filter_by(id=key_id, organization_id=current_user.organization_id).first()
    if not key:
        raise HTTPException(status_code=404, detail="API Key not found or belongs to another organization.")

    db.delete(key)
    db.commit()
    return {"status": "success", "message": "API Key revoked successfully."}
