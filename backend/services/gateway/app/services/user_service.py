from fastapi import HTTPException
from sqlalchemy.orm import Session
from common.database.models import User
from common.auth.jwt_utils import get_password_hash
from app.repository.user_repo import user_repo
from app.schemas.users import (
    UserResponse,
    UserCreateRequest,
    UserUpdateRequest,
    OrganizationResponse
)

class UserService:
    def list_users(self, current_user: User, db: Session) -> list[UserResponse]:
        role = current_user.role.capitalize()
        if role == "Superadmin":
            users = user_repo.list_all_users(db)
        else:
            users = user_repo.list_users_by_org(db, current_user.organization_id)

        results = []
        for u in users:
            org = user_repo.get_organization_by_id(db, u.organization_id)
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

    def create_user(self, req: UserCreateRequest, current_user: User, db: Session) -> UserResponse:
        # Check if user already exists
        existing = user_repo.get_user_by_email(db, req.email)
        if existing:
            raise HTTPException(status_code=400, detail="User with this email already exists.")

        # Resolve organization ID
        role = current_user.role.capitalize()
        if role == "Superadmin":
            org_id = req.organization_id if req.organization_id else current_user.organization_id
        else:
            org_id = current_user.organization_id

        # Verify organization exists
        org = user_repo.get_organization_by_id(db, org_id)
        if not org:
            raise HTTPException(status_code=400, detail="Selected organization does not exist.")

        new_user = user_repo.create_user(
            db=db,
            email=req.email,
            hashed_password=get_password_hash(req.password),
            role=req.role.capitalize(),
            org_id=org_id
        )

        return UserResponse(
            id=str(new_user.id),
            email=new_user.email,
            role=new_user.role,
            organization_id=str(new_user.organization_id),
            organization_name=org.name,
            created_at=new_user.created_at.isoformat()
        )

    def update_user(self, user_id: str, req: UserUpdateRequest, current_user: User, db: Session) -> UserResponse:
        user_to_update = user_repo.get_user_by_id(db, user_id)
        if not user_to_update:
            raise HTTPException(status_code=404, detail="User not found.")

        role = current_user.role.capitalize()
        # Check permissions
        if role != "Superadmin" and user_to_update.organization_id != current_user.organization_id:
            raise HTTPException(status_code=403, detail="Not authorized to update users in other organizations.")

        # Apply updates
        if req.email is not None:
            if req.email != user_to_update.email:
                existing = user_repo.get_user_by_email(db, req.email)
                if existing:
                    raise HTTPException(status_code=400, detail="Email is already in use.")
                user_to_update.email = req.email

        if req.role is not None:
            user_to_update.role = req.role.capitalize()

        if req.organization_id is not None:
            if role == "Superadmin":
                org = user_repo.get_organization_by_id(db, req.organization_id)
                if not org:
                    raise HTTPException(status_code=400, detail="Organization not found.")
                user_to_update.organization_id = req.organization_id
            else:
                raise HTTPException(status_code=403, detail="Only Superadmin can update user organization.")

        user_repo.commit(db)
        user_repo.refresh(db, user_to_update)

        org = user_repo.get_organization_by_id(db, user_to_update.organization_id)
        org_name = org.name if org else "Unknown"

        return UserResponse(
            id=str(user_to_update.id),
            email=user_to_update.email,
            role=user_to_update.role,
            organization_id=str(user_to_update.organization_id),
            organization_name=org_name,
            created_at=user_to_update.created_at.isoformat()
        )

    def delete_user(self, user_id: str, current_user: User, db: Session) -> dict:
        user_to_delete = user_repo.get_user_by_id(db, user_id)
        if not user_to_delete:
            raise HTTPException(status_code=404, detail="User not found.")

        role = current_user.role.capitalize()
        if role != "Superadmin" and user_to_delete.organization_id != current_user.organization_id:
            raise HTTPException(status_code=403, detail="Not authorized to delete users in other organizations.")

        # Prevent deleting self
        if str(user_to_delete.id) == str(current_user.id):
            raise HTTPException(status_code=400, detail="Cannot delete your own user account.")

        user_repo.delete_user(db, user_to_delete)
        return {"message": "User deleted successfully."}

    def list_organizations(self, current_user: User, db: Session) -> list[OrganizationResponse]:
        orgs = user_repo.list_all_organizations(db)
        return [OrganizationResponse(id=str(o.id), name=o.name) for o in orgs]

user_service = UserService()
