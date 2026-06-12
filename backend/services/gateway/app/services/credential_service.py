import logging
import httpx
from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.orm import Session
from common.database.models import User, PageCredential
from common.schemas.audit import PageCredentialConfig
from common.config import get_service_url
from app.repository.credential_repo import credential_repo
from app.schemas.credentials import CredentialCreate, CredentialResponse

logger = logging.getLogger(__name__)

CRAWLER_SERVICE_URL = get_service_url("CRAWLER_SERVICE_URL", "http://crawler:8003", "http://localhost:8003")

class CredentialService:
    def _mask_username(self, username: Optional[str]) -> Optional[str]:
        if not username:
            return None
        if "@" in username:
            parts = username.split("@", 1)
            name = parts[0]
            domain = parts[1]
            if len(name) <= 2:
                return name + "••••@" + domain
            return name[:2] + "••••@" + domain
        else:
            if len(username) <= 4:
                return username[:1] + "••••"
            return username[:3] + "••••"

    def _to_response(self, cred: PageCredential) -> CredentialResponse:
        username_decrypted = credential_repo.get_decrypted_username(cred)
        username_masked = self._mask_username(username_decrypted)
        has_extra_fields = cred.extra_fields_encrypted is not None

        return CredentialResponse(
            id=cred.id,
            project_id=cred.project_id,
            organization_id=cred.organization_id,
            label=cred.label,
            login_url=cred.login_url,
            url_pattern=cred.url_pattern,
            auth_type=cred.auth_type,
            username_masked=username_masked,
            username_field=cred.username_field,
            password_field=cred.password_field,
            submit_selector=cred.submit_selector,
            post_login_url_pattern=cred.post_login_url_pattern,
            has_extra_fields=has_extra_fields,
            created_at=cred.created_at,
            updated_at=cred.updated_at,
        )

    def list_credentials(self, project_id: UUID, current_user: User, db: Session) -> List[CredentialResponse]:
        # Enforce project org ownership check
        from common.database.models import Project
        proj = db.query(Project).filter_by(id=project_id, organization_id=current_user.organization_id).first()
        if not proj:
            raise HTTPException(status_code=404, detail="Project not found or belongs to another organization.")

        credentials = credential_repo.list_credentials(db, project_id, current_user.organization_id)
        return [self._to_response(c) for c in credentials]

    def get_credential(self, project_id: UUID, credential_id: UUID, current_user: User, db: Session) -> CredentialResponse:
        cred = credential_repo.get_credential_by_id(db, credential_id, current_user.organization_id)
        if not cred or cred.project_id != project_id:
            raise HTTPException(status_code=404, detail="Credential not found.")
        return self._to_response(cred)

    def create_credential(
        self, project_id: UUID, req: CredentialCreate, current_user: User, db: Session
    ) -> CredentialResponse:
        from common.database.models import Project
        proj = db.query(Project).filter_by(id=project_id, organization_id=current_user.organization_id).first()
        if not proj:
            raise HTTPException(status_code=404, detail="Project not found or belongs to another organization.")

        cred = credential_repo.create_credential(db, project_id, current_user.organization_id, req)
        return self._to_response(cred)

    def update_credential(
        self, project_id: UUID, credential_id: UUID, req: CredentialCreate, current_user: User, db: Session
    ) -> CredentialResponse:
        cred = credential_repo.get_credential_by_id(db, credential_id, current_user.organization_id)
        if not cred or cred.project_id != project_id:
            raise HTTPException(status_code=404, detail="Credential not found.")

        updated_cred = credential_repo.update_credential(db, credential_id, current_user.organization_id, req)
        if not updated_cred:
            raise HTTPException(status_code=404, detail="Credential not found.")
        return self._to_response(updated_cred)

    def delete_credential(self, project_id: UUID, credential_id: UUID, current_user: User, db: Session) -> dict:
        cred = credential_repo.get_credential_by_id(db, credential_id, current_user.organization_id)
        if not cred or cred.project_id != project_id:
            raise HTTPException(status_code=404, detail="Credential not found.")

        success = credential_repo.delete_credential(db, credential_id, current_user.organization_id)
        if not success:
            raise HTTPException(status_code=404, detail="Credential not found.")
        return {"status": "success", "message": "Credential configuration deleted successfully."}

    def resolve_for_audit(self, credential_id: UUID, org_id: UUID, db: Session) -> PageCredentialConfig:
        cred = credential_repo.get_credential_by_id(db, credential_id, org_id)
        if not cred:
            raise HTTPException(status_code=404, detail="Credential configuration not found.")

        username = credential_repo.get_decrypted_username(cred)
        password = credential_repo.get_decrypted_password(cred)
        extra_fields = credential_repo.get_decrypted_extra_fields(cred)

        return PageCredentialConfig(
            auth_type=cred.auth_type,
            login_url=cred.login_url,
            url_pattern=cred.url_pattern,
            username=username,
            password=password,
            username_field=cred.username_field,
            password_field=cred.password_field,
            submit_selector=cred.submit_selector,
            post_login_url_pattern=cred.post_login_url_pattern,
            extra_fields=extra_fields,
        )

    async def test_credential_login(
        self, project_id: UUID, credential_id: UUID, current_user: User, db: Session
    ) -> dict:
        config = self.resolve_for_audit(credential_id, current_user.organization_id, db)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{CRAWLER_SERVICE_URL}/test_login",
                    json=config.model_dump(mode="json"),
                    headers={"Content-Type": "application/json"}
                )
                if response.status_code != 200:
                    detail = response.text
                    try:
                        detail = response.json().get("detail", detail)
                    except Exception:
                        pass
                    raise HTTPException(status_code=response.status_code, detail=detail)
                return response.json()
            except HTTPException as he:
                raise he
            except httpx.HTTPStatusError as hse:
                raise HTTPException(status_code=hse.response.status_code, detail=hse.response.text)
            except Exception as e:
                logger.error(f"Failed to communicate with crawler service at {CRAWLER_SERVICE_URL}: {e}")
                raise HTTPException(status_code=502, detail=f"Failed to verify credentials: {str(e)}")

credential_service = CredentialService()
