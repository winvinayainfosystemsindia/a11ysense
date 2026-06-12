from datetime import datetime
from sqlalchemy.orm import Session
from common.database.models import ApiKey

class ApiKeyRepository:
    def list_keys(self, db: Session, org_id: str) -> list[ApiKey]:
        return (
            db.query(ApiKey)
            .filter_by(organization_id=org_id)
            .order_by(ApiKey.created_at.desc())
            .all()
        )

    def create_key(
        self,
        db: Session,
        key_hash: str,
        name: str,
        user_id: str,
        org_id: str,
        expires_at: datetime
    ) -> ApiKey:
        new_key = ApiKey(
            key_hash=key_hash,
            name=name,
            user_id=user_id,
            organization_id=org_id,
            expires_at=expires_at
        )
        db.add(new_key)
        db.commit()
        db.refresh(new_key)
        return new_key

    def get_key_by_id_and_org(self, db: Session, key_id: str, org_id: str) -> ApiKey | None:
        return db.query(ApiKey).filter_by(id=key_id, organization_id=org_id).first()

    def delete_key(self, db: Session, key: ApiKey) -> None:
        db.delete(key)
        db.commit()

api_key_repo = ApiKeyRepository()
