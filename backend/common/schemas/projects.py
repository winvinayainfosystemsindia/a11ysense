from datetime import datetime
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, Field

class ProjectCreate(BaseModel):
    name: str = Field(..., description="Project name")
    project_type: str = Field(default="web_page", pattern="^(web_page|web_application)$", description="Type of target: web_page or web_application")
    base_url: Optional[str] = Field(default=None, description="Starting base URL for project")

class ProjectResponse(BaseModel):
    id: UUID
    name: str
    project_type: str
    base_url: Optional[str] = None
    organization_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
