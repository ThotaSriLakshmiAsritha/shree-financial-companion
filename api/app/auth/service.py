from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.dependencies import AuthenticatedUser
from app.auth.models import Profile, UserIdentity, UserPreference


def normalize_phone_number(phone_number: str | None) -> str | None:
    if phone_number is None:
        return None
    normalized = "".join(character for character in phone_number.strip() if character.isdigit() or character == "+")
    return normalized or None


def _upsert_identity(db: Session, profile: Profile, provider: str, provider_subject: str) -> UserIdentity:
    identity = db.scalar(
        select(UserIdentity).where(
            UserIdentity.provider == provider,
            UserIdentity.provider_subject == provider_subject,
        )
    )
    if identity:
        if identity.user_id != profile.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This authentication identity is already linked to another user.",
            )
        return identity

    identity = UserIdentity(user_id=profile.id, provider=provider, provider_subject=provider_subject)
    db.add(identity)
    db.flush()
    return identity


def sync_identities(db: Session, profile: Profile, auth_user: AuthenticatedUser) -> list[UserIdentity]:
    identities = [("supabase", auth_user.subject)] + [
        (identity.provider, identity.subject) for identity in auth_user.identities
    ]
    result: list[UserIdentity] = []
    seen: set[tuple[str, str]] = set()
    try:
        for provider, provider_subject in identities:
            if (provider, provider_subject) in seen:
                continue
            seen.add((provider, provider_subject))
            result.append(_upsert_identity(db, profile, provider, provider_subject))
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This authentication identity is already linked to another user.",
        ) from exc
    return result


def ensure_profile(db: Session, auth_user: AuthenticatedUser) -> Profile:
    identity = db.scalar(
        select(UserIdentity).where(
            UserIdentity.provider == "supabase",
            UserIdentity.provider_subject == auth_user.subject,
        )
    )
    if identity:
        profile = db.get(Profile, identity.user_id)
        if profile is None:
            raise HTTPException(status_code=500, detail="Identity points to a missing profile.")
        if profile.phone_number is None and auth_user.phone:
            profile.phone_number = normalize_phone_number(auth_user.phone)
        sync_identities(db, profile, auth_user)
        db.commit()
        db.refresh(profile)
        return profile

    profile = Profile(
        display_name=auth_user.display_name,
        phone_number=normalize_phone_number(auth_user.phone),
        preferred_language=auth_user.preferred_language or "en",
    )
    db.add(profile)
    db.flush()
    db.add(UserPreference(user_id=profile.id))
    sync_identities(db, profile, auth_user)
    db.commit()
    db.refresh(profile)
    return profile


def update_profile(db: Session, profile: Profile, payload: dict[str, object]) -> Profile:
    preference_fields = {
        "preferred_channel",
        "voice_enabled",
        "monthly_income_estimate",
        "financial_setup_completed",
        "consent_accepted",
        "consent_version",
    }
    preference_updates = {key: payload.pop(key) for key in list(payload) if key in preference_fields}
    if payload.get("onboarding_completed") is True and not (
        preference_updates.get("consent_accepted") is True
        or (profile.preferences is not None and profile.preferences.consent_accepted)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Consent is required before completing onboarding.",
        )
    if preference_updates.get("consent_accepted") is True:
        preference_updates.setdefault("consent_version", "privacy-v1")
        preference_updates.setdefault("consent_at", datetime.now(timezone.utc))
    if payload.get("phone_number") is not None:
        payload["phone_number"] = normalize_phone_number(str(payload["phone_number"]))
    for key, value in payload.items():
        if value is not None:
            setattr(profile, key, value)
    preferences = profile.preferences or UserPreference(user_id=profile.id)
    for key, value in preference_updates.items():
        if value is not None:
            setattr(preferences, key, value)
    db.add(preferences)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Phone number is already registered.") from exc
    db.refresh(profile)
    return profile


def list_identities(db: Session, profile: Profile) -> list[UserIdentity]:
    return list(
        db.scalars(select(UserIdentity).where(UserIdentity.user_id == profile.id).order_by(UserIdentity.created_at))
    )


def resolve_profile_by_phone(db: Session, phone_number: str) -> Profile | None:
    normalized = normalize_phone_number(phone_number)
    if normalized is None:
        return None
    return db.scalar(select(Profile).where(Profile.phone_number == normalized))


def get_profile_by_id(db: Session, user_id: UUID) -> Profile | None:
    return db.get(Profile, user_id)
