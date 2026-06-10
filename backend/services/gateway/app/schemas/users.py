from typing import Optional
from pydantic import BaseModel, EmailStr, Field

class UserResponse(BaseModel):
    id: str
    email: str
    role: str
    organization_id: str
    organization_name: str
    created_at: str


class UserCreateRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: str = "Viewer"
    organization_id: Optional[str] = None


class UserUpdateRequest(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    organization_id: Optional[str] = None


class OrganizationResponse(BaseModel):
    id: str
    name: str
