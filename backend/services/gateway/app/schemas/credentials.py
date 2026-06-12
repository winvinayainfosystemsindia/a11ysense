from datetime import datetime
from uuid import UUID
from typing import Optional, Dict
from pydantic import BaseModel

class CredentialCreate(BaseModel):
    label: str
    login_url: str
    url_pattern: str
    auth_type: str = "form"  # form, cookie, bearer_token
    username: Optional[str] = None
    password: Optional[str] = None
    username_field: Optional[str] = "[name=username]"
    password_field: Optional[str] = "[name=password]"
    submit_selector: Optional[str] = "button[type=submit]"
    post_login_url_pattern: Optional[str] = None
    extra_fields: Optional[Dict[str, str]] = None

class CredentialResponse(BaseModel):
    id: UUID
    project_id: UUID
    organization_id: UUID
    label: str
    login_url: str
    url_pattern: str
    auth_type: str
    username_masked: Optional[str] = None
    username_field: Optional[str] = None
    password_field: Optional[str] = None
    submit_selector: Optional[str] = None
    post_login_url_pattern: Optional[str] = None
    has_extra_fields: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
