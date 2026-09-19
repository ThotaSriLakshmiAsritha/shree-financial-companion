import logging
from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel

from app.db.session import check_database_connection

router = APIRouter(tags=["system"])
logger = logging.getLogger(__name__)


class HealthResponse(BaseModel):
    status: str
    service: str
    database: str
    timestamp: datetime


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    try:
        database_status = "connected" if check_database_connection() else "unavailable"
    except Exception:
        logger.exception("Health check database probe failed")
        database_status = "unavailable"
    return HealthResponse(
        status="ok",
        service="sahachari-api",
        database=database_status,
        timestamp=datetime.now(timezone.utc),
    )
