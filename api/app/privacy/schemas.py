from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AccountDeletionRequest(BaseModel):
    confirmation: str = Field(pattern="^DELETE_MY_ACCOUNT$")


class AuditEventResponse(BaseModel):
    id: UUID
    event_type: str
    resource_type: str | None
    resource_id: UUID | None
    channel: str | None
    details: str | None
    metadata: dict[str, object] | None = Field(
        default=None,
        validation_alias="event_metadata",
        serialization_alias="metadata",
    )
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
