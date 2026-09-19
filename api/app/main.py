import logging
import re
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.auth import router as auth_router
from app.api.routes.context import router as context_router
from app.api.routes.conversation import router as conversation_router
from app.api.routes.financial import router as financial_router
from app.api.routes.health import router as health_router
from app.api.routes.metrics import router as metrics_router
from app.api.routes.privacy import router as privacy_router
from app.api.routes.stories import router as stories_router
from app.api.routes.voice import router as voice_router, sarvam_router
from app.core.config import get_settings
from app.core.errors import register_error_handlers
from app.core.logging import configure_logging

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s in %s mode", settings.app_name, settings.app_env)
    try:
        from app.db.base import Base
        from app.db.session import engine
        import app.auth.models, app.financial.models, app.context.models, app.privacy.models, app.voice.models  # noqa: F401
        Base.metadata.create_all(bind=engine)
    except Exception as exc:
        logger.warning("Auto table creation skipped or failed: %s", exc)
    yield
    logger.info("Stopping %s", settings.app_name)


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Foundation API for the Sahachari multilingual financial companion.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def observe_request_latency(request, call_next):
    started = time.perf_counter()
    ok = False
    try:
        response = await call_next(request)
        ok = response.status_code < 500
        return response
    finally:
        route = request.scope.get("route")
        route_name = getattr(route, "path", None) or re.sub(r"/[0-9a-f-]{16,}", "/:id", request.url.path)
        from app.core.metrics import metrics

        metrics.observe(
            "api.request",
            (time.perf_counter() - started) * 1000,
            ok=ok,
            label=f"{request.method} {route_name}",
        )
@app.get("/")
def root():
    return {
        "status": "ok",
        "service": settings.app_name,
        "docs": "/docs",
        "health": "/health",
    }


app.include_router(health_router)
app.include_router(auth_router)
app.include_router(context_router)
app.include_router(conversation_router)
app.include_router(voice_router)
app.include_router(sarvam_router)
app.include_router(financial_router)
app.include_router(stories_router)
app.include_router(privacy_router)
app.include_router(metrics_router)
register_error_handlers(app)
