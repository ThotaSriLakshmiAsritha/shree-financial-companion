from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Profile(Base):
    __tablename__ = "profiles"
    __table_args__ = (
        CheckConstraint("preferred_language IN ('en', 'hi', 'te')", name="ck_profiles_preferred_language"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    display_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    phone_number: Mapped[str | None] = mapped_column(String(32), nullable=True, unique=True)
    preferred_language: Mapped[str] = mapped_column(String(5), nullable=False, default="en", server_default="en")
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    identities: Mapped[list["UserIdentity"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )
    preferences: Mapped["UserPreference | None"] = relationship(
        back_populates="profile", cascade="all, delete-orphan", uselist=False
    )


class UserIdentity(Base):
    __tablename__ = "user_identities"
    __table_args__ = (
        UniqueConstraint("provider", "provider_subject", name="uq_user_identities_provider_subject"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String(40), nullable=False)
    provider_subject: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    profile: Mapped[Profile] = relationship(back_populates="identities")


class UserPreference(Base):
    __tablename__ = "user_preferences"

    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("profiles.id", ondelete="CASCADE"), primary_key=True
    )
    preferred_channel: Mapped[str] = mapped_column(String(30), nullable=False, default="web", server_default="web")
    voice_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    monthly_income_estimate: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    financial_setup_completed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    consent_accepted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    consent_version: Mapped[str | None] = mapped_column(String(40), nullable=True)
    consent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    profile: Mapped[Profile] = relationship(back_populates="preferences")
