"""
User Management Router
  GET /api/users                  — lists users (Superadmin sees all, Admin sees organization users)
  POST /api/users                 — creates a new user
  PUT /api/users/{user_id}        — updates user details
  DELETE /api/users/{user_id}     — deletes a user
  GET /api/organizations          — lists all organizations (Superadmin only)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from common.database import get_db
from common.database.models import User, Organization
from common.auth.deps import require_role
from common.auth.jwt_utils import get_password_hash
from app.schemas.users import (
    UserResponse,
    UserCreateRequest,
    UserUpdateRequest,
    OrganizationResponse
)

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
    role = current_user.role.capitalize()
    if role == "Superadmin":
        users = db.query(User).all()
    else:
        users = db.query(User).filter_by(organization_id=current_user.organization_id).all()

    results = []
    for u in users:
        org = db.query(Organization).filter_by(id=u.organization_id).first()
        org_name = org.name if org else "Unknown"
        results.append(UserResponse(
            id=str(u.id),
            email=u.email,
            role=u.role,
            organization_id=str(u.organization_id),
            organization_name=org_name,
            created_at=u.created_at.isoformat()
        ))
    return results


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
    # Check if user already exists
    existing = db.query(User).filter_by(email=req.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists.")

    # Resolve organization ID
    role = current_user.role.capitalize()
    if role == "Superadmin":
        org_id = req.organization_id if req.organization_id else current_user.organization_id
    else:
        org_id = current_user.organization_id

    # Verify organization exists
    org = db.query(Organization).filter_by(id=org_id).first()
    if not org:
        raise HTTPException(status_code=400, detail="Selected organization does not exist.")

    # Create user
    new_user = User(
        email=req.email,
        hashed_password=get_password_hash(req.password),
        role=req.role.capitalize(),
        organization_id=org_id
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return UserResponse(
        id=str(new_user.id),
        email=new_user.email,
        role=new_user.role,
        organization_id=str(new_user.organization_id),
        organization_name=org.name,
        created_at=new_user.created_at.isoformat()
    )


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
    user_to_update = db.query(User).filter_by(id=user_id).first()
    if not user_to_update:
        raise HTTPException(status_code=404, detail="User not found.")

    role = current_user.role.capitalize()
    # Check permissions
    if role != "Superadmin" and user_to_update.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Not authorized to update users in other organizations.")

    # Apply updates
    if req.email is not None:
        if req.email != user_to_update.email:
            existing = db.query(User).filter_by(email=req.email).first()
            if existing:
                raise HTTPException(status_code=400, detail="Email is already in use.")
            user_to_update.email = req.email

    if req.role is not None:
        user_to_update.role = req.role.capitalize()

    if req.organization_id is not None:
        if role == "Superadmin":
            org = db.query(Organization).filter_by(id=req.organization_id).first()
            if not org:
                raise HTTPException(status_code=400, detail="Organization not found.")
            user_to_update.organization_id = req.organization_id
        else:
            raise HTTPException(status_code=403, detail="Only Superadmin can update user organization.")

    db.commit()
    db.refresh(user_to_update)

    org = db.query(Organization).filter_by(id=user_to_update.organization_id).first()
    org_name = org.name if org else "Unknown"

    return UserResponse(
        id=str(user_to_update.id),
        email=user_to_update.email,
        role=user_to_update.role,
        organization_id=str(user_to_update.organization_id),
        organization_name=org_name,
        created_at=user_to_update.created_at.isoformat()
    )


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
    user_to_delete = db.query(User).filter_by(id=user_id).first()
    if not user_to_delete:
        raise HTTPException(status_code=404, detail="User not found.")

    role = current_user.role.capitalize()
    if role != "Superadmin" and user_to_delete.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete users in other organizations.")

    # Prevent deleting self
    if str(user_to_delete.id) == str(current_user.id):
        raise HTTPException(status_code=400, detail="Cannot delete your own user account.")

    db.delete(user_to_delete)
    db.commit()
    return {"message": "User deleted successfully."}


@router.get("/api/organizations", response_model=list[OrganizationResponse])
async def list_organizations(
    current_user: User = Depends(require_role(["Superadmin"])),
    db: Session = Depends(get_db)
):
    """
    List all organizations (Superadmin only).
    """
    orgs = db.query(Organization).all()
    return [OrganizationResponse(id=str(o.id), name=o.name) for o in orgs]
