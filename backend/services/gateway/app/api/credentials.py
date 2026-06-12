"""
Credentials Router — CRUD for page-specific audit credentials
"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from common.database import get_db
from common.database.models import User
from common.auth.deps import get_current_user, require_role
from app.schemas.credentials import CredentialCreate, CredentialResponse
from app.services.credential_service import credential_service

router = APIRouter(prefix="/api/projects/{project_id}/credentials", tags=["Credentials"])


# ── Routes ─────────────────────────────────────────────────────────────────

@router.get("", response_model=List[CredentialResponse])
async def list_credentials(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all credentials belonging to a project. Accessible by all organization members."""
    return credential_service.list_credentials(project_id, current_user, db)


@router.get("/{credential_id}", response_model=CredentialResponse)
async def get_credential(
    project_id: UUID,
    credential_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific credential (with username masked). Accessible by all organization members."""
    return credential_service.get_credential(project_id, credential_id, current_user, db)


@router.post("", response_model=CredentialResponse)
async def create_credential(
    project_id: UUID,
    req: CredentialCreate,
    current_user: User = Depends(require_role(["Auditor", "Admin"])),
    db: Session = Depends(get_db)
):
    """Create a new credential set for a project. Requires Auditor or Admin role."""
    return credential_service.create_credential(project_id, req, current_user, db)


@router.put("/{credential_id}", response_model=CredentialResponse)
async def update_credential(
    project_id: UUID,
    credential_id: UUID,
    req: CredentialCreate,
    current_user: User = Depends(require_role(["Auditor", "Admin"])),
    db: Session = Depends(get_db)
):
    """Update a credential configuration. Requires Auditor or Admin role."""
    return credential_service.update_credential(project_id, credential_id, req, current_user, db)


@router.delete("/{credential_id}")
async def delete_credential(
    project_id: UUID,
    credential_id: UUID,
    current_user: User = Depends(require_role(["Auditor", "Admin"])),
    db: Session = Depends(get_db)
):
    """Delete a credential configuration. Requires Auditor or Admin role."""
    return credential_service.delete_credential(project_id, credential_id, current_user, db)


@router.post("/{credential_id}/test")
async def test_credential_login(
    project_id: UUID,
    credential_id: UUID,
    current_user: User = Depends(require_role(["Auditor", "Admin"])),
    db: Session = Depends(get_db)
):
    """Test a credential login configuration by running a live Playwright login test. Requires Auditor or Admin."""
    return await credential_service.test_credential_login(project_id, credential_id, current_user, db)
