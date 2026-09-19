import logging
from dataclasses import dataclass, field
from typing import Annotated, Any

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db

logger = logging.getLogger(__name__)
bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthIdentity:
    provider: str
    subject: str


@dataclass(frozen=True)
class AuthenticatedUser:
    subject: str
    email: str | None = None
    phone: str | None = None
    display_name: str | None = None
    preferred_language: str | None = None
    identities: tuple[AuthIdentity, ...] = field(default_factory=tuple)


def _parse_identities(payload: dict[str, Any], subject: str) -> tuple[AuthIdentity, ...]:
    identities: list[AuthIdentity] = [AuthIdentity(provider="supabase", subject=subject)]
    for identity in payload.get("identities") or []:
        provider = identity.get("provider")
        identity_subject = identity.get("id")
        if provider and identity_subject:
            identities.append(AuthIdentity(provider=str(provider), subject=str(identity_subject)))
    unique: dict[tuple[str, str], AuthIdentity] = {(item.provider, item.subject): item for item in identities}
    return tuple(unique.values())


def verify_supabase_token(token: str) -> AuthenticatedUser:
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_anon_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase authentication is not configured.",
        )

    try:
        response = httpx.get(
            f"{settings.supabase_url.rstrip('/')}/auth/v1/user",
            headers={"apikey": settings.supabase_anon_key, "Authorization": f"Bearer {token}"},
            timeout=5.0,
        )
    except httpx.HTTPError as exc:
        logger.warning("Supabase auth verification failed to connect: %s", exc)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Authentication service unavailable.") from exc

    if response.status_code != 200:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session.")

    payload = response.json()
    subject = payload.get("id")
    if not subject:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session has no user subject.")

    metadata = payload.get("user_metadata") or {}
    preferred_language = metadata.get("preferred_language")
    return AuthenticatedUser(
        subject=str(subject),
        email=payload.get("email"),
        phone=payload.get("phone"),
        display_name=metadata.get("display_name") or metadata.get("full_name") or metadata.get("name"),
        preferred_language=preferred_language if preferred_language in {"en", "hi", "te"} else None,
        identities=_parse_identities(payload, str(subject)),
    )


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> AuthenticatedUser:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer session required.")
    return verify_supabase_token(credentials.credentials)


def get_current_profile(
    db: Annotated[Session, Depends(get_db)],
    auth_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
):
    from app.auth.service import ensure_profile

    return ensure_profile(db, auth_user)
