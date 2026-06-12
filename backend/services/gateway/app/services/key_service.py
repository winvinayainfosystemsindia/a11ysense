import uuid
import hashlib
from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlalchemy.orm import Session
from common.database.models import User, ApiKey
from app.repository.key_repo import api_key_repo
from app.schemas.keys import ApiKeyCreate, ApiKeyResponse, ApiKeyCreatedResponse

class ApiKeyService:
    def list_api_keys(self, current_user: User, db: Session) -> list[ApiKey]:
        return api_key_repo.list_keys(db, current_user.organization_id)

    def create_api_key(self, req: ApiKeyCreate, current_user: User, db: Session) -> ApiKeyCreatedResponse:
        raw_key = f"a11y_key_{uuid.uuid4().hex}{uuid.uuid4().hex[:16]}"
        hashed_key = hashlib.sha256(raw_key.encode()).hexdigest()

        expires_at = datetime.utcnow() + timedelta(days=req.expires_in_days)

        new_key = api_key_repo.create_key(
            db=db,
            key_hash=hashed_key,
            name=req.name,
            user_id=current_user.id,
            org_id=current_user.organization_id,
            expires_at=expires_at
        )

        return ApiKeyCreatedResponse(
            id=str(new_key.id),
            name=new_key.name,
            created_at=new_key.created_at,
            expires_at=new_key.expires_at,
            api_key=raw_key
        )

    def revoke_api_key(self, key_id: str, current_user: User, db: Session) -> dict:
        key = api_key_repo.get_key_by_id_and_org(db, key_id, current_user.organization_id)
        if not key:
            raise HTTPException(status_code=404, detail="API Key not found or belongs to another organization.")

        api_key_repo.delete_key(db, key)
        return {"status": "success", "message": "API Key revoked successfully."}

api_key_service = ApiKeyService()
