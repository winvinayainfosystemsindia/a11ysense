"""
User Management API endpoints.
Provides CRUD operations for users within the authenticated user's organization.
"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from common.database.connection import get_db
from common.database.models import User, Organization
from common.auth.deps import get_current_user, require_role
from backend.app.schemas.user import UserCreate, UserUpdate, UserResponse
from backend.app.services.user_service import user_service

router = APIRouter(tags=["Users"])

@router.get("/api/users", response_model=List[UserResponse])
async def list_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all users in the current organization."""
    return user_service.get_users_by_org(db, current_user.organization_id)

@router.post("/api/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    req: UserCreate,
    current_user: User = Depends(require_role(["Admin"])),
    db: Session = Depends(get_db)
):
    """Create a new user within the organization (Admin only)."""
    return user_service.create_user(db, req, current_user.organization_id)

@router.get("/api/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get details of a specific user."""
    user = user_service.get_user_by_id(db, user_id, current_user.organization_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/api/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    req: UserUpdate,
    current_user: User = Depends(require_role(["Admin"])),
    db: Session = Depends(get_db)
):
    """Update a user's role, email, or password (Admin only)."""
    user = user_service.update_user(db, user_id, req, current_user.organization_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.delete("/api/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    current_user: User = Depends(require_role(["Admin"])),
    db: Session = Depends(get_db)
):
    """Delete a user from the organization (Admin only)."""
    success = user_service.delete_user(db, user_id, current_user.organization_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")

@router.get("/api/organizations")
async def list_organizations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List organizations for user administration."""
    orgs = db.query(Organization).all()
    return [{"id": str(o.id), "name": o.name, "created_at": o.created_at.isoformat()} for o in orgs]
