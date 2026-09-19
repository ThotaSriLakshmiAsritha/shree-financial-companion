from fastapi import APIRouter, HTTPException, status

from app.core.config import get_settings
from app.core.metrics import metrics

router = APIRouter(prefix="/metrics", tags=["observability"])


@router.get("/performance")
def read_performance_metrics() -> dict[str, object]:
    if get_settings().app_env.lower() in {"staging", "production"}:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found.")
    return {"metrics": metrics.snapshot()}
