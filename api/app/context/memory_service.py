import re
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.context.models import Memory
from app.context.schemas import MemoryContextSlice, MemoryCreate

_WORD_PATTERN = re.compile(r"[\w']+", re.UNICODE)


def create_memory(db: Session, user_id: UUID, payload: MemoryCreate) -> Memory:
    memory = Memory(user_id=user_id, **payload.model_dump())
    db.add(memory)
    db.commit()
    db.refresh(memory)
    return memory


def retrieve_relevant_memories(
    db: Session,
    user_id: UUID,
    query: str | None = None,
    limit: int = 3,
) -> list[MemoryContextSlice]:
    """Retrieve a bounded, ranked slice; never expose the full memory table to the LLM."""
    candidates = list(
        db.scalars(
            select(Memory)
            .where(Memory.user_id == user_id)
            .order_by(Memory.importance.desc(), Memory.created_at.desc())
            .limit(50)
        )
    )
    query_terms = set(_WORD_PATTERN.findall((query or "").lower()))
    now = datetime.now(timezone.utc)

    def overlap_for(memory: Memory) -> int:
        memory_terms = set(_WORD_PATTERN.findall(memory.content.lower()))
        return len(query_terms & memory_terms)

    def score(memory: Memory) -> tuple[float, datetime]:
        overlap = overlap_for(memory) if query_terms else 0
        created_at = memory.created_at or now
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        age_days = max((now - created_at).total_seconds() / 86400, 0)
        recency = 1 / (1 + age_days)
        return (overlap * 10 + float(memory.importance or 0) + recency * 0.1, created_at)

    relevant_candidates = [memory for memory in candidates if overlap_for(memory) > 0] if query_terms else candidates
    selected = sorted(relevant_candidates or candidates, key=score, reverse=True)[:limit]
    return [
        MemoryContextSlice(
            content=memory.content,
            memory_type=memory.memory_type,
            importance=memory.importance,
        )
        for memory in selected
    ]
