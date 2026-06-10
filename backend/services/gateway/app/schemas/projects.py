from datetime import datetime
from uuid import UUID
from pydantic import BaseModel

class ProjectCreate(BaseModel):
    name: str


class ProjectResponse(BaseModel):
    id: UUID
    name: str
    organization_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
