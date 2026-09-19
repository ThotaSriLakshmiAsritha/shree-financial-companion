from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AuditEvent(Base):
    """Server-side audit trail without collecting IP addresses or user agents by default."""

    __tablename__ = "audit_events"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    # Nullable so an account-deletion event can survive deletion of the profile.
    user_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("profiles.id", ondelete="SET NULL"), nullable=True, index=True
    )
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    resource_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    resource_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    channel: Mapped[str | None] = mapped_column(String(30), nullable=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    event_metadata: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
