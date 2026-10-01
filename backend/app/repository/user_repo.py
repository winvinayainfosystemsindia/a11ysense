from sqlalchemy.orm import Session
from common.database.models import User, Organization

class UserRepository:
    def list_all_users(self, db: Session) -> list[User]:
        return db.query(User).all()

    def list_users_by_org(self, db: Session, org_id: str) -> list[User]:
        return db.query(User).filter_by(organization_id=org_id).all()

    def get_organization_by_id(self, db: Session, org_id: str) -> Organization | None:
        return db.query(Organization).filter_by(id=org_id).first()

    def get_user_by_email(self, db: Session, email: str) -> User | None:
        return db.query(User).filter_by(email=email).first()

    def create_user(
        self,
        db: Session,
        email: str,
        hashed_password: str,
        role: str,
        org_id: str
    ) -> User:
        new_user = User(
            email=email,
            hashed_password=hashed_password,
            role=role,
            organization_id=org_id
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    def get_user_by_id(self, db: Session, user_id: str) -> User | None:
        return db.query(User).filter_by(id=user_id).first()

    def delete_user(self, db: Session, user: User) -> None:
        db.delete(user)
        db.commit()

    def list_all_organizations(self, db: Session) -> list[Organization]:
        return db.query(Organization).all()

    def commit(self, db: Session) -> None:
        db.commit()

    def refresh(self, db: Session, obj: any) -> None:
        db.refresh(obj)

user_repo = UserRepository()
