import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class AppError(Exception):
    def __init__(self, message: str, status_code: int = 400, code: str = "application_error") -> None:
        self.message = message
        self.status_code = status_code
        self.code = code
        super().__init__(message)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled request error: %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "internal_server_error", "message": "An unexpected error occurred."}},
        )

