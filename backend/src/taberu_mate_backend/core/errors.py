import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from taberu_mate_backend.core.config import Settings
from taberu_mate_backend.core.security_events import log_security_event

logger = logging.getLogger("taberu_mate.errors")
_PRODUCTION_ENVIRONMENTS = {"production", "prod", "staging"}


def configure_error_handlers(app: FastAPI, settings: Settings) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        if _is_production_like(settings):
            log_security_event("request_validation_failed", request=request, reason="bad_request")
            return JSONResponse(status_code=400, content={"detail": "Bad request"})

        return JSONResponse(status_code=422, content={"detail": exc.errors()})

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(
        request: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        if not _is_production_like(settings):
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail},
                headers=exc.headers,
            )

        status_code, detail = _production_error(exc.status_code)
        if status_code in {400, 403, 429}:
            log_security_event("http_error", request=request, reason=str(exc.status_code))
        return JSONResponse(
            status_code=status_code, content={"detail": detail}, headers=exc.headers
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled application error")
        log_security_event("unhandled_exception", request=request, reason=type(exc).__name__)
        if _is_production_like(settings):
            return JSONResponse(status_code=400, content={"detail": "Bad request"})
        raise exc


def _is_production_like(settings: Settings) -> bool:
    return settings.environment.lower() in _PRODUCTION_ENVIRONMENTS


def _production_error(status_code: int) -> tuple[int, str]:
    if status_code == 429:
        return 429, "Too many requests"
    if status_code in {401, 403}:
        return 403, "Forbidden"
    return 400, "Bad request"
