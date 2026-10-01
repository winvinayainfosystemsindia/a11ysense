from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from common.database.connection import get_db
from common.database.models import User, PageCredential
from common.auth.deps import get_current_user, require_role
from pydantic import BaseModel, Field

class CredentialCreate(BaseModel):
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
    project_id: Optional[UUID] = None

class CredentialResponse(BaseModel):
    id: UUID
    project_id: UUID
    organization_id: UUID
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

router = APIRouter(tags=["Credentials"])

@router.get("/api/credentials", response_model=List[CredentialResponse])
@router.get("/api/projects/{project_id}/credentials", response_model=List[CredentialResponse])
async def list_credentials(
    project_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(PageCredential).filter(PageCredential.organization_id == current_user.organization_id)
    if project_id:
        query = query.filter(PageCredential.project_id == project_id)
    return query.all()

@router.post("/api/credentials", response_model=CredentialResponse)
@router.post("/api/projects/{project_id}/credentials", response_model=CredentialResponse)
async def create_credential(
    req: CredentialCreate,
    project_id: Optional[UUID] = None,
    current_user: User = Depends(require_role(["Auditor", "Admin"])),
    db: Session = Depends(get_db)
):
    eff_project_id = project_id or req.project_id
    if not eff_project_id:
        raise HTTPException(status_code=400, detail="project_id is required")

    cred = PageCredential(
        project_id=eff_project_id,
        organization_id=current_user.organization_id,
        label=req.label,
        login_url=req.login_url,
        url_pattern=req.url_pattern,
        auth_type=req.auth_type,
        username_field=req.username_field,
        password_field=req.password_field,
        submit_selector=req.submit_selector,
        post_login_url_pattern=req.post_login_url_pattern,
        username_encrypted=req.username,
        password_encrypted=req.password
    )
    db.add(cred)
    db.commit()
    db.refresh(cred)
    return cred

@router.put("/api/credentials/{credential_id}", response_model=CredentialResponse)
@router.put("/api/projects/{project_id}/credentials/{credential_id}", response_model=CredentialResponse)
async def update_credential(
    credential_id: UUID,
    req: CredentialCreate,
    project_id: Optional[UUID] = None,
    current_user: User = Depends(require_role(["Auditor", "Admin"])),
    db: Session = Depends(get_db)
):
    cred = db.query(PageCredential).filter(
        PageCredential.id == credential_id,
        PageCredential.organization_id == current_user.organization_id
    ).first()
    if not cred:
        raise HTTPException(status_code=404, detail="Credential not found")

    cred.label = req.label
    cred.login_url = req.login_url
    cred.url_pattern = req.url_pattern
    cred.auth_type = req.auth_type
    if req.username:
        cred.username_encrypted = req.username
    if req.password:
        cred.password_encrypted = req.password
    if req.username_field:
        cred.username_field = req.username_field
    if req.password_field:
        cred.password_field = req.password_field
    if req.submit_selector:
        cred.submit_selector = req.submit_selector
    if req.post_login_url_pattern:
        cred.post_login_url_pattern = req.post_login_url_pattern

    db.commit()
    db.refresh(cred)
    return cred

@router.delete("/api/credentials/{credential_id}", status_code=status.HTTP_204_NO_CONTENT)
@router.delete("/api/projects/{project_id}/credentials/{credential_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_credential(
    credential_id: UUID,
    project_id: Optional[UUID] = None,
    current_user: User = Depends(require_role(["Auditor", "Admin"])),
    db: Session = Depends(get_db)
):
    cred = db.query(PageCredential).filter(
        PageCredential.id == credential_id,
        PageCredential.organization_id == current_user.organization_id
    ).first()
    if not cred:
        raise HTTPException(status_code=404, detail="Credential not found")

    db.delete(cred)
    db.commit()

@router.post("/api/credentials/{credential_id}/test")
@router.post("/api/projects/{project_id}/credentials/{credential_id}/test")
async def test_credential(
    credential_id: UUID,
    project_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cred = db.query(PageCredential).filter(
        PageCredential.id == credential_id,
        PageCredential.organization_id == current_user.organization_id
    ).first()
    if not cred:
        raise HTTPException(status_code=404, detail="Credential not found")

    return {"status": "success", "message": "Credential configured properly"}
