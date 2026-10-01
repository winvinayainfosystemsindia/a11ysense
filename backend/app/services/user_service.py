"""
User Management Service for A11ySense Monolith.
Handles listing, creating, updating, and deleting users within an organization.
"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from common.database.models import User
from backend.app.schemas.user import UserCreate, UserUpdate
from backend.app.services.auth_service import get_password_hash

class UserService:
    def get_users_by_org(self, db: Session, org_id: UUID) -> List[User]:
        return db.query(User).filter(User.organization_id == org_id).all()

    def get_user_by_id(self, db: Session, user_id: UUID, org_id: UUID) -> Optional[User]:
        return db.query(User).filter(User.id == user_id, User.organization_id == org_id).first()

    def create_user(self, db: Session, user_in: UserCreate, org_id: UUID) -> User:
        user = User(
            email=user_in.email,
            hashed_password=get_password_hash(user_in.password),
            role=user_in.role,
            organization_id=org_id
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def update_user(self, db: Session, user_id: UUID, user_in: UserUpdate, org_id: UUID) -> Optional[User]:
        user = self.get_user_by_id(db, user_id, org_id)
        if not user:
            return None

        if user_in.email:
            user.email = user_in.email
        if user_in.role:
            user.role = user_in.role
        if user_in.password:
            user.hashed_password = get_password_hash(user_in.password)

        db.commit()
        db.refresh(user)
        return user

    def delete_user(self, db: Session, user_id: UUID, org_id: UUID) -> bool:
        user = self.get_user_by_id(db, user_id, org_id)
        if not user:
            return False
        db.delete(user)
        db.commit()
        return True

user_service = UserService()
