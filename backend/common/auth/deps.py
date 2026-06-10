import hashlib
from typing import Optional
from fastapi import Depends, HTTPException, status, Header, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from common.database.connection import get_db
from common.database.models import User, ApiKey
from common.auth.jwt_utils import decode_access_token

security = HTTPBearer(auto_error=False)

def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db)
) -> User:
    """
    Unified security dependency supporting:
    1. JWT Bearer Tokens in Authorization Header (Browser / GUI)
    2. API Keys in 'X-API-Key' Header (CI/CD Pipelines)
    3. Checked downstream context headers (X-User-ID etc.) for trusted inter-service calls.
    """
    # 1. Check if we have downstream context propagated from gateway
    user_id_hdr = request.headers.get("X-User-ID")
    if user_id_hdr:
        user = db.query(User).filter(User.id == user_id_hdr).first()
        if user:
            return user

    # 2. Check X-API-Key first (for API/CI/CD integrations)
    if x_api_key:
        # Key format: 'a11y_key_...'
        key_hash = hashlib.sha256(x_api_key.strip().encode()).hexdigest()
        api_key_record = db.query(ApiKey).filter(ApiKey.key_hash == key_hash).first()
        if api_key_record:
            # Check expiration if set
            from datetime import datetime
            if api_key_record.expires_at and api_key_record.expires_at < datetime.utcnow():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="API Key has expired"
                )
            
            # Fetch user associated with key
            user = db.query(User).filter(User.id == api_key_record.user_id).first()
            if user:
                return user
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )

    # 3. Check JWT Bearer token
    token = None
    if credentials:
        token = credentials.credentials
    else:
        token = request.query_params.get("token")

    if token:
        payload = decode_access_token(token)
        if payload:
            email = payload.get("sub")
            if email:
                user = db.query(User).filter(User.email == email).first()
                if user:
                    return user
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
    RBAC dependency factory that validates the user's role.
    Role hierarchy/privilege validation can also be performed.
    """
    def dependency(current_user: User = Depends(get_current_user)):
        role = current_user.role.capitalize()
        # Normalise list
        normalised_allowed = [r.capitalize() for r in allowed_roles]
        
        # Superadmin bypasses all checks
        if role == "Superadmin":
            return current_user
            
        # Admin can do anything if Admin is allowed
        if "Admin" in normalised_allowed and role == "Admin":
            return current_user
        
        if role not in normalised_allowed and role != "Admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: one of {allowed_roles}"
            )
        return current_user
    return dependency
