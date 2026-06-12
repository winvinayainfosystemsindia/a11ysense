"""
User Management Router
  GET /api/users                  — lists users (Superadmin sees all, Admin sees organization users)
  POST /api/users                 — creates a new user
  PUT /api/users/{user_id}        — updates user details
  DELETE /api/users/{user_id}     — deletes a user
  GET /api/organizations          — lists all organizations (Superadmin only)
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from common.database import get_db
from common.database.models import User
from common.auth.deps import require_role
from app.schemas.users import (
    UserResponse,
    UserCreateRequest,
    UserUpdateRequest,
    OrganizationResponse
)
from app.services.user_service import user_service

router = APIRouter(tags=["User Management"])


# ── Routes ─────────────────────────────────────────────────────────────────

@router.get("/api/users", response_model=list[UserResponse])
async def list_users(
    current_user: User = Depends(require_role(["Admin", "Superadmin"])),
    db: Session = Depends(get_db)
):
    """
    List users:
    - Superadmin: sees all users across the entire system.
    - Admin: sees only users belonging to their own organization.
    """
    return user_service.list_users(current_user, db)


@router.post("/api/users", response_model=UserResponse)
async def create_user(
    req: UserCreateRequest,
    current_user: User = Depends(require_role(["Admin", "Superadmin"])),
    db: Session = Depends(get_db)
):
    """
    Create user:
    - Superadmin: can specify any organization_id.
    - Admin: organization_id is hardlocked to current user's organization.
    """
    return user_service.create_user(req, current_user, db)


@router.put("/api/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    req: UserUpdateRequest,
    current_user: User = Depends(require_role(["Admin", "Superadmin"])),
    db: Session = Depends(get_db)
):
    """
    Update user:
    - Superadmin: can update any user's email, role, or organization.
    - Admin: can only update users within their own organization (no organization change).
    """
    return user_service.update_user(user_id, req, current_user, db)


@router.delete("/api/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_role(["Admin", "Superadmin"])),
    db: Session = Depends(get_db)
):
    """
    Delete user:
    - Superadmin: can delete any user.
    - Admin: can only delete users in their own organization.
    - Cannot delete own logged-in user.
    """
    return user_service.delete_user(user_id, current_user, db)


@router.get("/api/organizations", response_model=list[OrganizationResponse])
async def list_organizations(
    current_user: User = Depends(require_role(["Superadmin"])),
    db: Session = Depends(get_db)
):
    """
    List all organizations (Superadmin only).
    """
    return user_service.list_organizations(current_user, db)
