from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class IdentityResponse(BaseModel):
    provider: str
    provider_subject: str

    model_config = ConfigDict(from_attributes=True)


class PreferencesResponse(BaseModel):
    preferred_channel: str
    voice_enabled: bool
    monthly_income_estimate: float | None
    financial_setup_completed: bool
    consent_accepted: bool
    consent_version: str | None
    consent_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class ProfileResponse(BaseModel):
    id: UUID
    display_name: str | None
    phone_number: str | None
    preferred_language: str
    onboarding_completed: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuthMeResponse(BaseModel):
    profile: ProfileResponse
    identities: list[IdentityResponse]
    preferences: PreferencesResponse


class ProfileUpdateRequest(BaseModel):
    display_name: str | None = Field(default=None, max_length=120)
    phone_number: str | None = Field(default=None, max_length=32)
    preferred_language: str | None = Field(default=None, pattern="^(en|hi|te)$")
    onboarding_completed: bool | None = None
    preferred_channel: str | None = Field(default=None, pattern="^(web|voice|feature_phone)$")
    voice_enabled: bool | None = None
    monthly_income_estimate: float | None = Field(default=None, ge=0)
    financial_setup_completed: bool | None = None
    consent_accepted: bool | None = None
    consent_version: str | None = Field(default=None, max_length=40)


class PhoneResolutionResponse(BaseModel):
    user_id: UUID
    preferred_language: str
    onboarding_completed: bool
