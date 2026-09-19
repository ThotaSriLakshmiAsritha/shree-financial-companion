from collections.abc import Generator

from app.auth.dependencies import AuthenticatedUser, get_current_user
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool


def test_protected_profile_route_uses_internal_uuid_and_preferences() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    def override_db() -> Generator[Session, None, None]:
        with Session(engine) as db:
            yield db

    auth_user = AuthenticatedUser(subject="supabase-user-route-test")
    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = lambda: auth_user

    try:
        with TestClient(app) as client:
            response = client.get("/auth/me", headers={"Authorization": "Bearer test-token"})
            assert response.status_code == 200
            body = response.json()
            assert body["profile"]["id"]
            assert body["identities"][0]["provider"] == "supabase"
            assert body["preferences"]["voice_enabled"] is True

            updated = client.patch(
                "/auth/me",
                headers={"Authorization": "Bearer test-token"},
                json={
                    "preferred_language": "te",
                    "phone_number": "+91 98765 43210",
                    "onboarding_completed": True,
                    "consent_accepted": True,
                },
            )
            assert updated.status_code == 200
            updated_body = updated.json()
            assert updated_body["profile"]["preferred_language"] == "te"
            assert updated_body["preferences"]["consent_accepted"] is True
    finally:
        app.dependency_overrides.clear()

