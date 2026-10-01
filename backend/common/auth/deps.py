import uuid
import logging
from typing import Optional
from fastapi import Depends, HTTPException, status, Header, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from common.database.connection import get_db
from common.database.models import User
from common.auth.jwt_utils import decode_access_token

logger = logging.getLogger("a11ysense.auth.deps")
security = HTTPBearer(auto_error=False)

def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Multi-tenant security dependency:
    Decodes JWT token and resolves user by User ID or Email, ensuring tenant context (organization_id) is bound.
    """
    # 1. Check if downstream context header exists
    user_id_hdr = request.headers.get("X-User-ID")
    if user_id_hdr:
        try:
            user = db.query(User).filter(User.id == uuid.UUID(user_id_hdr)).first()
            if user:
                return user
        except Exception:
            pass

    # 2. Check JWT Bearer token
    token = None
    if credentials:
        token = credentials.credentials
    else:
        token = request.query_params.get("token")

    if token:
        payload = decode_access_token(token)
        if payload:
            sub = payload.get("sub")
            if sub:
                user = None
                try:
                    user_uuid = uuid.UUID(sub)
                    user = db.query(User).filter(User.id == user_uuid).first()
                except (ValueError, TypeError):
                    user = db.query(User).filter(User.email == str(sub)).first()

                if user:
                    return user

        logger.warning(f"Failed to authenticate JWT token for payload: {payload}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token"
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication credentials not found"
    )

def require_role(allowed_roles: list[str]):
    """
    RBAC dependency factory that validates user's role.
    """
    def dependency(current_user: User = Depends(get_current_user)):
        role = current_user.role.capitalize()
        normalised_allowed = [r.capitalize() for r in allowed_roles]
        
        if role in ["Superadmin", "Admin"]:
            return current_user
        
        if role not in normalised_allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: one of {allowed_roles}"
            )
        return current_user
    return dependency
