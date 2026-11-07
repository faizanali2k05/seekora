import hmac
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from app.core.config import Settings, get_settings


@dataclass(frozen=True, slots=True)
class Principal:
    subject: str
    role: str


def _extract_api_key(request: Request) -> str | None:
    authorization = request.headers.get("authorization", "")
    if authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    return request.headers.get("x-api-key")


def resolve_principal(request: Request, settings: Settings) -> Principal | None:
    supplied = _extract_api_key(request)
    if not supplied:
        return None
    expected = settings.admin_api_key.get_secret_value()
    if hmac.compare_digest(supplied.encode(), expected.encode()):
        return Principal(subject="local-admin", role="admin")
    return None


def require_admin(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
) -> Principal:
    principal = resolve_principal(request, settings)
    if principal is None or principal.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A valid administrator API key is required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return principal
