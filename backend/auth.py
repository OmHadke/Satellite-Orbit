from typing import Any, Dict, Iterable, Optional

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from config import get_settings

security = HTTPBearer(auto_error=False)


def _validate_claims(payload: Dict[str, Any]) -> None:
    settings = get_settings()
    if settings.jwt_audience:
        audience = payload.get("aud")
        if audience != settings.jwt_audience:
            raise HTTPException(status_code=401, detail="Invalid token audience")
    if settings.jwt_issuer:
        issuer = payload.get("iss")
        if issuer != settings.jwt_issuer:
            raise HTTPException(status_code=401, detail="Invalid token issuer")


def decode_jwt_token(token: str) -> Dict[str, Any]:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            options={"verify_aud": bool(settings.jwt_audience)},
        )
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc
    _validate_claims(payload)
    return payload


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Dict[str, Any]:
    settings = get_settings()
    if not settings.auth_enabled:
        request.state.user = {"sub": "anonymous"}
        return request.state.user

    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Missing bearer token")

    payload = decode_jwt_token(credentials.credentials)
    request.state.user = payload
    return payload


def require_roles(required_roles: Iterable[str]):
    async def _require_roles(
        user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        roles = user.get("roles", [])
        if not required_roles:
            return user
        if not isinstance(roles, list):
            raise HTTPException(status_code=403, detail="Invalid roles claim")
        if not set(required_roles).issubset(set(roles)):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user

    return _require_roles
