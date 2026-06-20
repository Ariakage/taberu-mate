import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from taberu_mate_backend.core.config import Settings, get_settings
from taberu_mate_backend.core.security import (
    AuthTokenError,
    CsrfTokenError,
    decode_access_token,
    verify_csrf_token,
)
from taberu_mate_backend.core.security_events import log_security_event
from taberu_mate_backend.crud.tokens import is_access_token_revoked
from taberu_mate_backend.crud.users import get_user_by_id
from taberu_mate_backend.db.session import get_connection
from taberu_mate_backend.models.user import User


@dataclass(frozen=True, slots=True)
class AuthenticatedUser:
    user: User
    access_jti: str
    access_expires_at: datetime


def get_current_auth(
    request: Request,
    connection: Annotated[sqlite3.Connection, Depends(get_connection)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthenticatedUser:
    token = _extract_access_token(request, settings)
    if token is None:
        log_security_event("access_token_missing", request=request)
        raise _invalid_credentials()

    try:
        token_payload = decode_access_token(token, settings)
    except AuthTokenError as exc:
        log_security_event("access_token_invalid", request=request)
        raise _invalid_credentials() from exc

    if is_access_token_revoked(connection, token_payload.jti):
        log_security_event(
            "access_token_revoked",
            request=request,
            user_id=str(token_payload.user_id),
            jti=token_payload.jti,
        )
        raise _invalid_credentials()

    user = get_user_by_id(connection, token_payload.user_id)
    if user is None:
        log_security_event(
            "access_token_user_missing",
            request=request,
            user_id=str(token_payload.user_id),
            jti=token_payload.jti,
        )
        raise _invalid_credentials()

    return AuthenticatedUser(
        user=user,
        access_jti=token_payload.jti,
        access_expires_at=token_payload.expires_at,
    )


def get_current_user(
    current_auth: Annotated[AuthenticatedUser, Depends(get_current_auth)],
) -> User:
    return current_auth.user


def verify_csrf(request: Request, settings: Annotated[Settings, Depends(get_settings)]) -> None:
    try:
        verify_csrf_token(
            request.cookies.get(settings.csrf_cookie_name),
            request.headers.get(settings.csrf_header_name),
        )
    except CsrfTokenError as exc:
        log_security_event("csrf_token_invalid", request=request)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid CSRF token",
        ) from exc


def _extract_access_token(request: Request, settings: Settings) -> str | None:
    authorization = request.headers.get("authorization")
    if authorization is not None:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() == "bearer" and token:
            return token.strip()

    return request.cookies.get(settings.access_token_cookie_name)


def _invalid_credentials() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
