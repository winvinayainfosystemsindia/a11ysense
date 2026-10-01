from sqlalchemy.orm import Session
from common.database.models import User, Organization, Project

class AuthRepository:
    def get_user_by_email(self, db: Session, email: str) -> User | None:
        return db.query(User).filter_by(email=email).first()

    def get_organization_by_name(self, db: Session, name: str) -> Organization | None:
        return db.query(Organization).filter_by(name=name).first()

    def get_organization_by_id(self, db: Session, org_id: str) -> Organization | None:
        return db.query(Organization).filter_by(id=org_id).first()

    def create_organization(self, db: Session, name: str) -> Organization:
        org = Organization(name=name)
        db.add(org)
        db.flush()
        return org

    def get_default_project_by_org(self, db: Session, org_id: str) -> Project | None:
        return db.query(Project).filter_by(name="Default Project", organization_id=org_id).first()

    def create_project(self, db: Session, name: str, org_id: str) -> Project:
        proj = Project(name=name, organization_id=org_id)
        db.add(proj)
        return proj

    def create_user(
        self,
        db: Session,
        email: str,
        hashed_password: str,
        role: str,
        org_id: str
    ) -> User:
        user = User(
            email=email,
            hashed_password=hashed_password,
            role=role,
            organization_id=org_id
        )
        db.add(user)
        return user

auth_repo = AuthRepository()
