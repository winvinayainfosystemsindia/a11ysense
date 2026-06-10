import uuid
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

class ApiKeyCreate(BaseModel):
    name: str
    expires_in_days: int = Field(default=30, ge=1, le=365)


class ApiKeyResponse(BaseModel):
    id: uuid.UUID
    name: str
    created_at: datetime
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ApiKeyCreatedResponse(ApiKeyResponse):
    api_key: str  # Displayed ONLY once upon creation
