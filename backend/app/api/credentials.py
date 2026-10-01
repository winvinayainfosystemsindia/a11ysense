from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from common.database.connection import get_db
from common.database.models import User, PageCredential
from common.auth.deps import get_current_user, require_role
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Dict

class CredentialCreate(BaseModel):
    project_id: UUID
    label: str
    login_url: str
    url_pattern: str
    auth_type: str = Field(default="form", pattern="^(form|cookie|bearer_token)$")
    username: Optional[str] = None
    password: Optional[str] = None
    username_field: Optional[str] = "[name=username]"
    password_field: Optional[str] = "[name=password]"
    submit_selector: Optional[str] = "button[type=submit]"
    post_login_url_pattern: Optional[str] = None

class CredentialResponse(BaseModel):
    id: UUID
    project_id: UUID
    label: str
    login_url: str
    url_pattern: str
    auth_type: str
    username_field: Optional[str] = None
    password_field: Optional[str] = None
    submit_selector: Optional[str] = None
    post_login_url_pattern: Optional[str] = None

    class Config:
        from_attributes = True

router = APIRouter(prefix="/api/credentials", tags=["Credentials"])

@router.get("", response_model=List[CredentialResponse])
async def list_credentials(
    project_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(PageCredential).filter(PageCredential.organization_id == current_user.organization_id)
    if project_id:
        query = query.filter(PageCredential.project_id == project_id)
    return query.all()

@router.post("", response_model=CredentialResponse)
async def create_credential(
    req: CredentialCreate,
    current_user: User = Depends(require_role(["Auditor", "Admin"])),
    db: Session = Depends(get_db)
):
    cred = PageCredential(
        project_id=req.project_id,
        organization_id=current_user.organization_id,
        label=req.label,
        login_url=req.login_url,
        url_pattern=req.url_pattern,
        auth_type=req.auth_type,
        username_field=req.username_field,
        password_field=req.password_field,
        submit_selector=req.submit_selector,
        post_login_url_pattern=req.post_login_url_pattern,
        username_encrypted=req.username, # simplified in monolith
        password_encrypted=req.password
    )
    db.add(cred)
    db.commit()
    db.refresh(cred)
    return cred
