from typing import Optional
from pydantic import BaseModel, EmailStr, Field

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    organization_name: Optional[str] = None
    role: Optional[str] = "Viewer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: str
    email: str
    organization_id: str
    organization_name: str


class UserProfile(BaseModel):
    id: str
    email: str
    role: str
    organization_id: str
    organization_name: str


class VerifyTokenRequest(BaseModel):
    token: str


class VerifyTokenResponse(BaseModel):
    valid: bool
    user: Optional[UserProfile] = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str
