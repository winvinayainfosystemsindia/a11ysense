from datetime import datetime
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, EmailStr, Field

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    organization_name: str = Field(..., min_length=2)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserProfile(BaseModel):
    id: UUID
    email: str
    role: str
    organization_id: UUID
    organization_name: str
    created_at: datetime

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserProfile

class VerifyTokenRequest(BaseModel):
    token: str

class VerifyTokenResponse(BaseModel):
    valid: bool
    user: Optional[UserProfile] = None
    error: Optional[str] = None

class RefreshTokenRequest(BaseModel):
    refresh_token: str
