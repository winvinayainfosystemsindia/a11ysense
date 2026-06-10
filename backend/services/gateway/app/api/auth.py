"""
Auth Router — /auth/register, /auth/login, /auth/me
"""
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

import jwt
from common.database import get_db
from common.database.models import User, Organization, Project
from common.auth.jwt_utils import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    JWT_SECRET,
    JWT_ALGORITHM
)
from common.auth.deps import get_current_user
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    UserProfile,
    VerifyTokenRequest,
    VerifyTokenResponse,
    RefreshTokenRequest
)

router = APIRouter(prefix="/auth", tags=["Authentication"])



# ── Routes ─────────────────────────────────────────────────────────────────

@router.post("/register", response_model=UserProfile)
async def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user, creating an organization and default project."""
    existing_user = db.query(User).filter_by(email=req.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="A user with this email is already registered.")

    # Resolve or create organization
    org_name = req.organization_name or f"{req.email.split('@')[0]}'s Workspace"
    org = db.query(Organization).filter_by(name=org_name).first()
    is_new_org = False
    if not org:
        org = Organization(name=org_name)
        db.add(org)
        db.flush()  # Allocate ID
        is_new_org = True

    # Create the default project for the organization if new
    default_proj = db.query(Project).filter_by(name="Default Project", organization_id=org.id).first()
    if not default_proj:
        db.add(Project(name="Default Project", organization_id=org.id))

    # Grant 500 credits welcome bonus to new organizations
    if is_new_org:
        from common.billing.billing_manager import billing_manager
        try:
            billing_manager.grant_welcome_bonus(db, org.id)
        except Exception as e:
            print(f"Failed to grant welcome bonus: {e}")

    # Build user and save
    new_user = User(
        email=req.email,
        hashed_password=get_password_hash(req.password),
        role=req.role.capitalize() if req.role else "Viewer",
        organization_id=org.id
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return UserProfile(
        id=str(new_user.id),
        email=new_user.email,
        role=new_user.role,
        organization_id=str(org.id),
        organization_name=org.name
    )


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user and return a signed JWT access token."""
    user = db.query(User).filter_by(email=req.email).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")

    org = db.query(Organization).filter_by(id=user.organization_id).first()
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


@router.get("/me", response_model=UserProfile)
async def get_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Return the currently authenticated user's profile."""
    org = db.query(Organization).filter_by(id=current_user.organization_id).first()
    org_name = org.name if org else "Workspace"
    return UserProfile(
        id=str(current_user.id),
        email=current_user.email,
        role=current_user.role,
        organization_id=str(current_user.organization_id),
        organization_name=org_name
    )


@router.post("/verify", response_model=VerifyTokenResponse)
async def verify_token(req: VerifyTokenRequest, db: Session = Depends(get_db)):
    """Verifies access token signature and expiry, and returns user profile if valid."""
    decoded_token = decode_access_token(req.token)
    if not decoded_token:
        return VerifyTokenResponse(valid=False, user=None)
        
    email = decoded_token.get("sub")
    if not email:
        return VerifyTokenResponse(valid=False, user=None)
        
    user = db.query(User).filter_by(email=email).first()
    if not user:
        return VerifyTokenResponse(valid=False, user=None)
        
    org = db.query(Organization).filter_by(id=user.organization_id).first()
    org_name = org.name if org else "Workspace"
    
    user_profile = UserProfile(
        id=str(user.id),
        email=user.email,
        role=user.role,
        organization_id=str(user.organization_id),
        organization_name=org_name
    )
    return VerifyTokenResponse(valid=True, user=user_profile)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(req: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Verifies refresh token signature and expiry, and issues new access/refresh tokens (rotation)."""
    payload = decode_refresh_token(req.refresh_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    
    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token payload")
        
    user = db.query(User).filter_by(email=email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    org = db.query(Organization).filter_by(id=user.organization_id).first()
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

