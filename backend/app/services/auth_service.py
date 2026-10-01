from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import jwt

from common.database.models import User, Organization, Project
from backend.app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, UserProfile, VerifyTokenRequest, VerifyTokenResponse, RefreshTokenRequest
from common.auth.jwt_utils import create_access_token, create_refresh_token, decode_access_token, decode_refresh_token

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def register(self, req: RegisterRequest, db: Session) -> UserProfile:
        existing_user = db.query(User).filter(User.email == req.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="User with this email already exists")

        org = db.query(Organization).filter(Organization.name == req.organization_name).first()
        if not org:
            org = Organization(name=req.organization_name)
            db.add(org)
            db.flush()
            
            # Default project
            proj = Project(name="Default Project", project_type="web_page", organization_id=org.id)
            db.add(proj)

        user = User(
            email=req.email,
            hashed_password=pwd_context.hash(req.password),
            role="Admin",
            organization_id=org.id
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        return UserProfile(
            id=user.id,
            email=user.email,
            role=user.role,
            organization_id=user.organization_id,
            organization_name=org.name,
            created_at=user.created_at
        )

    def login(self, req: LoginRequest, db: Session) -> TokenResponse:
        user = db.query(User).filter(User.email == req.email).first()
        if not user or not pwd_context.verify(req.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        access_token = create_access_token(data={"sub": str(user.id), "org_id": str(user.organization_id), "role": user.role})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})

        org_name = user.organization.name if user.organization else "Enterprise"

        user_profile = UserProfile(
            id=user.id,
            email=user.email,
            role=user.role,
            organization_id=user.organization_id,
            organization_name=org_name,
            created_at=user.created_at
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            email=user.email,
            role=user.role,
            organization_id=user.organization_id,
            organization_name=org_name,
            user=user_profile
        )

    def get_me(self, current_user: User, db: Session) -> UserProfile:
        org_name = current_user.organization.name if current_user.organization else "Enterprise"
        return UserProfile(
            id=current_user.id,
            email=current_user.email,
            role=current_user.role,
            organization_id=current_user.organization_id,
            organization_name=org_name,
            created_at=current_user.created_at
        )

    def verify_token(self, req: VerifyTokenRequest, db: Session) -> VerifyTokenResponse:
        try:
            payload = decode_access_token(req.token)
            if not payload:
                return VerifyTokenResponse(valid=False, error="Invalid token")
            user_id = payload.get("sub")
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return VerifyTokenResponse(valid=False, error="User not found")
            org_name = user.organization.name if user.organization else "Enterprise"
            return VerifyTokenResponse(
                valid=True,
                user=UserProfile(
                    id=user.id,
                    email=user.email,
                    role=user.role,
                    organization_id=user.organization_id,
                    organization_name=org_name,
                    created_at=user.created_at
                )
            )
        except Exception as e:
            return VerifyTokenResponse(valid=False, error=str(e))

    def refresh_token(self, req: RefreshTokenRequest, db: Session) -> TokenResponse:
        try:
            payload = decode_refresh_token(req.refresh_token)
            if not payload:
                raise HTTPException(status_code=401, detail="Invalid refresh token")
            user_id = payload.get("sub")
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(status_code=401, detail="User not found")

            access_token = create_access_token(data={"sub": str(user.id), "org_id": str(user.organization_id), "role": user.role})
            new_refresh = create_refresh_token(data={"sub": str(user.id)})

            org_name = user.organization.name if user.organization else "Enterprise"

            user_profile = UserProfile(
                id=user.id,
                email=user.email,
                role=user.role,
                organization_id=user.organization_id,
                organization_name=org_name,
                created_at=user.created_at
            )

            return TokenResponse(
                access_token=access_token,
                refresh_token=new_refresh,
                token_type="bearer",
                email=user.email,
                role=user.role,
                organization_id=user.organization_id,
                organization_name=org_name,
                user=user_profile
            )
        except Exception as e:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

auth_service = AuthService()
