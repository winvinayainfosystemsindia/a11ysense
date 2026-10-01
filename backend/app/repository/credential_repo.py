import os
import json
import base64
import logging
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from cryptography.fernet import Fernet
from common.database.models import PageCredential
from app.schemas.credentials import CredentialCreate

logger = logging.getLogger(__name__)

class CredentialRepository:
    def __init__(self):
        # Base64 encoded 32-byte key
        key_str = os.getenv("CREDENTIAL_ENCRYPTION_KEY")
        if not key_str:
            logger.warning("CREDENTIAL_ENCRYPTION_KEY not set! Using development fallback key.")
            # YV92ZXJ5X3N0YWJsZV9kZXZfc2VjcmV0X2tleV8zMmI= decodes to b"a_very_stable_dev_secret_key_32b"
            key_bytes = b"YV92ZXJ5X3N0YWJsZV9kZXZfc2VjcmV0X2tleV8zMmI="
        else:
            try:
                key_bytes = key_str.encode("utf-8")
                # Validate key
                Fernet(key_bytes)
            except Exception as e:
                logger.error(f"Invalid CREDENTIAL_ENCRYPTION_KEY: {e}. Using development fallback.")
                key_bytes = b"YV92ZXJ5X3N0YWJsZV9kZXZfc2VjcmV0X2tleV8zMmI="
        self.fernet = Fernet(key_bytes)

    def _encrypt(self, text: Optional[str]) -> Optional[str]:
        if not text:
            return None
        return self.fernet.encrypt(text.encode("utf-8")).decode("utf-8")

    def _decrypt(self, ciphertext: Optional[str]) -> Optional[str]:
        if not ciphertext:
            return None
        try:
            return self.fernet.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
        except Exception as e:
            logger.error(f"Failed to decrypt credential field: {e}")
            return None

    def list_credentials(self, db: Session, project_id: UUID, org_id: UUID) -> List[PageCredential]:
        return (
            db.query(PageCredential)
            .filter_by(project_id=project_id, organization_id=org_id)
            .order_by(PageCredential.created_at.desc())
            .all()
        )

    def get_credential_by_id(self, db: Session, credential_id: UUID, org_id: UUID) -> Optional[PageCredential]:
        return (
            db.query(PageCredential)
            .filter_by(id=credential_id, organization_id=org_id)
            .first()
        )

    def create_credential(
        self, db: Session, project_id: UUID, org_id: UUID, data: CredentialCreate
    ) -> PageCredential:
        extra_fields_str = None
        if data.extra_fields:
            extra_fields_str = json.dumps(data.extra_fields)

        new_credential = PageCredential(
            project_id=project_id,
            organization_id=org_id,
            label=data.label,
            login_url=data.login_url,
            url_pattern=data.url_pattern,
            auth_type=data.auth_type,
            username_field=data.username_field,
            password_field=data.password_field,
            submit_selector=data.submit_selector,
            username_encrypted=self._encrypt(data.username),
            password_encrypted=self._encrypt(data.password),
            extra_fields_encrypted=self._encrypt(extra_fields_str),
            post_login_url_pattern=data.post_login_url_pattern,
        )
        db.add(new_credential)
        db.commit()
        db.refresh(new_credential)
        return new_credential

    def update_credential(
        self, db: Session, credential_id: UUID, org_id: UUID, data: CredentialCreate
    ) -> Optional[PageCredential]:
        cred = self.get_credential_by_id(db, credential_id, org_id)
        if not cred:
            return None

        cred.label = data.label
        cred.login_url = data.login_url
        cred.url_pattern = data.url_pattern
        cred.auth_type = data.auth_type
        cred.username_field = data.username_field
        cred.password_field = data.password_field
        cred.submit_selector = data.submit_selector
        cred.post_login_url_pattern = data.post_login_url_pattern

        if data.username is not None:
            cred.username_encrypted = self._encrypt(data.username)
        if data.password is not None:
            cred.password_encrypted = self._encrypt(data.password)
        if data.extra_fields is not None:
            extra_fields_str = json.dumps(data.extra_fields) if data.extra_fields else None
            cred.extra_fields_encrypted = self._encrypt(extra_fields_str)

        db.commit()
        db.refresh(cred)
        return cred

    def delete_credential(self, db: Session, credential_id: UUID, org_id: UUID) -> bool:
        cred = self.get_credential_by_id(db, credential_id, org_id)
        if not cred:
            return False
        db.delete(cred)
        db.commit()
        return True

    def get_decrypted_username(self, cred: PageCredential) -> Optional[str]:
        return self._decrypt(cred.username_encrypted)

    def get_decrypted_password(self, cred: PageCredential) -> Optional[str]:
        return self._decrypt(cred.password_encrypted)

    def get_decrypted_extra_fields(self, cred: PageCredential) -> Optional[dict]:
        decrypted = self._decrypt(cred.extra_fields_encrypted)
        if not decrypted:
            return None
        try:
            return json.loads(decrypted)
        except Exception as e:
            logger.error(f"Failed to parse decrypted extra fields: {e}")
            return None

credential_repo = CredentialRepository()
