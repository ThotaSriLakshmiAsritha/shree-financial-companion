from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.context.models import EducationalContext
from app.context.schemas import (
    EducationalContextResponse,
    EducationalContextSlice,
    EducationalContextUpsert,
)
from app.education.state_machine import assert_transition


def upsert_educational_context(
    db: Session,
    user_id: UUID,
    payload: EducationalContextUpsert,
) -> EducationalContext:
    item = db.scalar(
        select(EducationalContext).where(
            EducationalContext.user_id == user_id,
            EducationalContext.concept == payload.concept,
        )
    )
    if item is None:
        item = EducationalContext(user_id=user_id, concept=payload.concept)
        db.add(item)
    else:
        assert_transition(item.knowledge_state, payload.knowledge_state)

    values = payload.model_dump()
    values["knowledge_state"] = payload.knowledge_state.value
    if payload.application_state is not None:
        values["application_state"] = payload.application_state.value
    for field, value in values.items():
        setattr(item, field, value)
    item.last_discussed = datetime.now(timezone.utc)
    db.commit()
    db.refresh(item)
    return item


def list_educational_context(
    db: Session,
    user_id: UUID,
    limit: int = 6,
) -> list[EducationalContextSlice]:
    items = list(
        db.scalars(
            select(EducationalContext)
            .where(EducationalContext.user_id == user_id)
            .order_by(EducationalContext.reinforcement_needed.desc(), EducationalContext.updated_at.desc())
            .limit(limit)
        )
    )
    return [
        EducationalContextSlice(
            concept=item.concept,
            knowledge_state=item.knowledge_state,
            application_state=item.application_state,
            reinforcement_needed=item.reinforcement_needed,
            reasoning=item.reasoning,
        )
        for item in items
    ]


def serialize_educational_context(item: EducationalContext) -> EducationalContextResponse:
    return EducationalContextResponse.model_validate(item)
