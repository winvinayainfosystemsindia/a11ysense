from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from common.database.connection import get_db
from common.database.models import User
from common.auth.deps import get_current_user
from backend.app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    UserProfile,
    VerifyTokenRequest,
    VerifyTokenResponse,
    RefreshTokenRequest
)
from backend.app.services.auth_service import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserProfile)
async def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user, creating an organization and default project."""
    return auth_service.register(req, db)

@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user and return a signed JWT access token."""
    return auth_service.login(req, db)

@router.get("/me", response_model=UserProfile)
async def get_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Return the currently authenticated user's profile."""
    return auth_service.get_me(current_user, db)

@router.post("/verify", response_model=VerifyTokenResponse)
async def verify_token(req: VerifyTokenRequest, db: Session = Depends(get_db)):
    """Verifies access token signature and expiry."""
    return auth_service.verify_token(req, db)

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(req: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Issues new access token using refresh token."""
    return auth_service.refresh_token(req, db)
