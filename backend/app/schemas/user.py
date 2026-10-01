"""
User schemas for Pydantic validation.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    email: EmailStr
    role: str = "Viewer"  # Admin, Auditor, Viewer

class UserCreate(UserBase):
    password: str
    organization_id: Optional[UUID] = None

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    password: Optional[str] = None

class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    role: str
    organization_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
