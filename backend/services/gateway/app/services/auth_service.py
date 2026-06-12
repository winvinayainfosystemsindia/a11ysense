from fastapi import HTTPException
from sqlalchemy.orm import Session

from common.database.models import User
from common.auth.jwt_utils import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token
)
from app.repository.auth_repo import auth_repo
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    UserProfile,
    VerifyTokenRequest,
    VerifyTokenResponse,
    RefreshTokenRequest
)

class AuthService:
    def register(self, req: RegisterRequest, db: Session) -> UserProfile:
        existing_user = auth_repo.get_user_by_email(db, req.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="A user with this email is already registered.")

        org_name = req.organization_name or f"{req.email.split('@')[0]}'s Workspace"
        org = auth_repo.get_organization_by_name(db, org_name)
        is_new_org = False
        if not org:
            org = auth_repo.create_organization(db, org_name)
            is_new_org = True

        default_proj = auth_repo.get_default_project_by_org(db, org.id)
        if not default_proj:
            auth_repo.create_project(db, "Default Project", org.id)

        if is_new_org:
            from common.billing.billing_manager import billing_manager
            try:
                billing_manager.grant_welcome_bonus(db, org.id)
            except Exception as e:
                print(f"Failed to grant welcome bonus: {e}")

        role = req.role.capitalize() if req.role else "Viewer"
        new_user = auth_repo.create_user(
            db=db,
            email=req.email,
            hashed_password=get_password_hash(req.password),
            role=role,
            org_id=org.id
        )
        db.commit()
        db.refresh(new_user)

        return UserProfile(
            id=str(new_user.id),
            email=new_user.email,
            role=new_user.role,
            organization_id=str(org.id),
            organization_name=org.name
        )

    def login(self, req: LoginRequest, db: Session) -> TokenResponse:
        user = auth_repo.get_user_by_email(db, req.email)
        if not user or not verify_password(req.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Incorrect email or password.")

        org = auth_repo.get_organization_by_id(db, user.organization_id)
        org_name = org.name if org else "Workspace"

        token_data = {
            "sub": user.email,
            "role": user.role,
            "org_id": str(user.organization_id)
        }
        access_token = create_access_token(data=token_data)
        refresh_token = create_refresh_token(data=token_data)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            role=user.role,
            email=user.email,
            organization_id=str(user.organization_id),
            organization_name=org_name
        )

    def get_me(self, current_user: User, db: Session) -> UserProfile:
        org = auth_repo.get_organization_by_id(db, current_user.organization_id)
        org_name = org.name if org else "Workspace"
        return UserProfile(
            id=str(current_user.id),
            email=current_user.email,
            role=current_user.role,
            organization_id=str(current_user.organization_id),
            organization_name=org_name
        )

    def verify_token(self, req: VerifyTokenRequest, db: Session) -> VerifyTokenResponse:
        decoded_token = decode_access_token(req.token)
        if not decoded_token:
            return VerifyTokenResponse(valid=False, user=None)

        email = decoded_token.get("sub")
        if not email:
            return VerifyTokenResponse(valid=False, user=None)

        user = auth_repo.get_user_by_email(db, email)
        if not user:
            return VerifyTokenResponse(valid=False, user=None)

        org = auth_repo.get_organization_by_id(db, user.organization_id)
        org_name = org.name if org else "Workspace"

        user_profile = UserProfile(
            id=str(user.id),
            email=user.email,
            role=user.role,
            organization_id=str(user.organization_id),
            organization_name=org_name
        )
        return VerifyTokenResponse(valid=True, user=user_profile)

    def refresh_token(self, req: RefreshTokenRequest, db: Session) -> TokenResponse:
        payload = decode_refresh_token(req.refresh_token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token payload")

        user = auth_repo.get_user_by_email(db, email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        org = auth_repo.get_organization_by_id(db, user.organization_id)
        org_name = org.name if org else "Workspace"

        token_data = {
            "sub": user.email,
            "role": user.role,
            "org_id": str(user.organization_id)
        }
        access_token = create_access_token(data=token_data)
        new_refresh_token = create_refresh_token(data=token_data)

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            role=user.role,
            email=user.email,
            organization_id=str(user.organization_id),
            organization_name=org_name
        )

auth_service = AuthService()
