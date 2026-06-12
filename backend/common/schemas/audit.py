from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID

class PageCredentialConfig(BaseModel):
    auth_type: str  # "form", "cookie", "bearer_token"
    login_url: str
    url_pattern: str
    username: Optional[str] = None
    password: Optional[str] = None
    username_field: Optional[str] = "[name=username]"
    password_field: Optional[str] = "[name=password]"
    submit_selector: Optional[str] = "button[type=submit]"
    post_login_url_pattern: Optional[str] = None
    extra_fields: Optional[Dict[str, str]] = None

class AuditRequest(BaseModel):
    url: str
    depth: int = Field(default=1, ge=1, le=5)
    audit_type: str = Field(default="standard", pattern="^(standard|comprehensive)$")
    credentials_id: Optional[UUID] = None
    credential_config: Optional[PageCredentialConfig] = None

class Violation(BaseModel):
    id: str
    impact: Optional[str]
    description: str
    help: str
    helpUrl: Optional[str] = None
    nodes: List[Dict[str, Any]]
    metadata: Dict[str, Any] = {}

class AuditResult(BaseModel):
    url: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    violations: List[Violation]
    passes: Optional[List[Any]] = None
    incomplete: Optional[List[Any]] = None
    inapplicable: Optional[List[Any]] = None
    metadata: Dict[str, Any] = {}
class AuditTask(BaseModel):
    task_id: str
    status: str
    url: Optional[str] = None
    report_url: Optional[str] = None
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    pages_found: Optional[int] = 0
    pages_completed: Optional[int] = 0
    pages_total: Optional[int] = 0
    pages_scanned: Optional[List[str]] = None
    pages_discovered: Optional[List[str]] = None
    error: Optional[str] = None
    token_usage: Optional[Dict[str, Any]] = None
    summary: Optional[Dict[str, Any]] = None

