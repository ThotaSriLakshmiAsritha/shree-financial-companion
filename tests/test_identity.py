from app.auth.dependencies import AuthenticatedUser, AuthIdentity
from app.auth.models import UserIdentity, UserPreference
from app.auth.service import ensure_profile, resolve_profile_by_phone, update_profile
from app.db.base import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import Session


def test_google_and_phone_mapping_resolve_to_one_internal_user() -> None:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)

    with Session(engine) as db:
        authenticated_user = AuthenticatedUser(
            subject="supabase-user-123",
            email="person@example.com",
            identities=(AuthIdentity(provider="google", subject="google-subject-123"),),
        )
        profile = ensure_profile(db, authenticated_user)
        update_profile(
            db,
            profile,
            {
                "display_name": "Lakshmi",
                "phone_number": "+91 98765 43210",
                "preferred_language": "te",
                "onboarding_completed": True,
                "consent_accepted": True,
            },
        )

        restored_profile = ensure_profile(db, authenticated_user)
        phone_profile = resolve_profile_by_phone(db, "+91-98765-43210")

        assert restored_profile.id == profile.id
        assert phone_profile is not None
        assert phone_profile.id == profile.id
        assert phone_profile.preferred_language == "te"
        assert db.query(UserIdentity).filter_by(user_id=profile.id).count() == 2
        assert db.query(UserPreference).filter_by(user_id=profile.id).count() == 1
