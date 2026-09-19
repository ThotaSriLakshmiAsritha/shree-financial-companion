from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import (
    AuthenticatedUser,
    get_current_profile,
    get_current_user,
)
from app.auth.models import Profile
from app.auth.schemas import (
    AuthMeResponse,
    PhoneResolutionResponse,
    PreferencesResponse,
    ProfileResponse,
    ProfileUpdateRequest,
)
from app.auth.service import (
    ensure_profile,
    list_identities,
    resolve_profile_by_phone,
    update_profile,
)
from app.db.session import get_db
from app.privacy.service import record_audit_event

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.get("/me", response_model=AuthMeResponse)
def get_me(
    db: Annotated[Session, Depends(get_db)],
    auth_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
) -> AuthMeResponse:
    profile = ensure_profile(db, auth_user)
    preferences = profile.preferences
    if preferences is None:
        raise HTTPException(status_code=500, detail="User preferences are missing.")
    return AuthMeResponse(
        profile=profile,
        identities=list_identities(db, profile),
        preferences=PreferencesResponse.model_validate(preferences),
    )


@router.patch("/me", response_model=AuthMeResponse)
def patch_me(
    payload: ProfileUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
    profile: Annotated[Profile, Depends(get_current_profile)],
) -> AuthMeResponse:
    changes = payload.model_dump(exclude_unset=True)
    updated = update_profile(db, profile, changes)
    if "consent_accepted" in payload.model_fields_set:
        record_audit_event(
            db,
            updated.id,
            "consent.updated",
            resource_type="user_preferences",
            metadata={
                "accepted": updated.preferences.consent_accepted if updated.preferences else False,
                "version": updated.preferences.consent_version if updated.preferences else None,
            },
        )
    preferences = updated.preferences
    if preferences is None:
        raise HTTPException(status_code=500, detail="User preferences are missing.")
    return AuthMeResponse(
        profile=ProfileResponse.model_validate(updated),
        identities=list_identities(db, updated),
        preferences=PreferencesResponse.model_validate(preferences),
    )


@router.post("/phone/resolve", response_model=PhoneResolutionResponse)
def resolve_phone(
    phone_number: str,
    db: Annotated[Session, Depends(get_db)],
    _auth_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
) -> PhoneResolutionResponse:
    profile = resolve_profile_by_phone(db, phone_number)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Phone number is not registered.")
    return PhoneResolutionResponse(
        user_id=profile.id,
        preferred_language=profile.preferred_language,
        onboarding_completed=profile.onboarding_completed,
    )
