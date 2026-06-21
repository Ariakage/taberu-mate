import secrets
import sqlite3
from datetime import UTC, datetime
from typing import Annotated, Literal, cast

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status

from taberu_mate_backend.api.deps import get_current_user, verify_csrf
from taberu_mate_backend.core.config import Settings, get_settings
from taberu_mate_backend.core.rate_limit import is_rate_limited, reset_rate_limit
from taberu_mate_backend.core.security import (
    AuthTokenError,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    generate_csrf_token,
    hash_password,
    hash_token,
    verify_password,
)
from taberu_mate_backend.core.security_events import log_security_event
from taberu_mate_backend.crud.profiles import (
    count_order_history,
    create_order_history,
    get_user_profile,
    list_order_history,
    upsert_user_profile,
)
from taberu_mate_backend.crud.tokens import (
    get_refresh_token,
    revoke_access_token,
    revoke_refresh_token,
    store_refresh_token,
)
from taberu_mate_backend.crud.users import create_user, get_user_by_id, get_user_by_username
from taberu_mate_backend.db.session import get_connection
from taberu_mate_backend.models.profile import OrderHistory, UserProfile
from taberu_mate_backend.models.user import User
from taberu_mate_backend.schemas.profile import (
    OrderHistoryCreate,
    OrderHistoryPublic,
    UserDashboardResponse,
    UserDashboardStats,
    UserProfilePublic,
    UserProfileUpdate,
)
from taberu_mate_backend.schemas.user import (
    CsrfTokenResponse,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserPublic,
)

router = APIRouter(tags=["Users"])
CookieSameSite = Literal["lax", "strict", "none"]


@router.get("/auth/csrf", response_model=CsrfTokenResponse, summary="Issue CSRF token")
def issue_csrf_token(
    response: Response,
    settings: Annotated[Settings, Depends(get_settings)],
) -> CsrfTokenResponse:
    csrf_token = generate_csrf_token()
    _set_csrf_cookie(response, settings, csrf_token)
    return CsrfTokenResponse(csrf_token=csrf_token)


@router.post(
    "/auth/register",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Register a user",
)
def register_user(
    payload: UserCreate,
    connection: Annotated[sqlite3.Connection, Depends(get_connection)],
    settings: Annotated[Settings, Depends(get_settings)],
    _csrf_verified: Annotated[None, Depends(verify_csrf)],
) -> User:
    if get_user_by_username(connection, payload.username) is not None:
        raise _username_conflict()

    password_hash = hash_password(payload.password)
    avatar_url = str(payload.avatar_url) if payload.avatar_url is not None else None

    try:
        return create_user(
            connection,
            username=payload.username,
            nickname=payload.nickname or payload.username,
            avatar_url=avatar_url,
            password_salt=password_hash.salt,
            password_hash=password_hash.password_hash,
        )
    except sqlite3.IntegrityError as exc:
        raise _username_conflict() from exc


@router.post("/auth/login", response_model=TokenResponse, summary="Log in")
def login_user(
    request: Request,
    response: Response,
    payload: UserLogin,
    connection: Annotated[sqlite3.Connection, Depends(get_connection)],
    settings: Annotated[Settings, Depends(get_settings)],
    _csrf_verified: Annotated[None, Depends(verify_csrf)],
) -> TokenResponse:
    rate_limit_key = _rate_limit_key(request, payload.username)
    if is_rate_limited(
        key=rate_limit_key,
        limit=settings.auth_login_rate_limit,
        window_seconds=settings.auth_login_rate_limit_window_seconds,
    ):
        log_security_event("login_rate_limited", request=request, username=payload.username)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many requests"
        )

    user = get_user_by_username(connection, payload.username)
    if user is None or not verify_password(
        payload.password,
        user.password_salt,
        user.password_hash,
    ):
        log_security_event("login_failed", request=request, username=payload.username)
        raise _invalid_credentials()

    reset_rate_limit(key=rate_limit_key)
    log_security_event(
        "login_succeeded", request=request, username=payload.username, user_id=str(user.id)
    )
    token_response, _refresh_jti = _issue_session(
        connection=connection,
        request=request,
        response=response,
        user=user,
        settings=settings,
    )
    return token_response


@router.post("/auth/refresh", response_model=TokenResponse, summary="Refresh session")
def refresh_session(
    request: Request,
    response: Response,
    connection: Annotated[sqlite3.Connection, Depends(get_connection)],
    settings: Annotated[Settings, Depends(get_settings)],
    _csrf_verified: Annotated[None, Depends(verify_csrf)],
) -> TokenResponse:
    refresh_token = request.cookies.get(settings.refresh_token_cookie_name)
    if refresh_token is None:
        log_security_event("refresh_token_missing", request=request)
        raise _invalid_credentials()

    try:
        refresh_payload = decode_refresh_token(refresh_token, settings)
    except AuthTokenError as exc:
        log_security_event("refresh_token_invalid", request=request)
        raise _invalid_credentials() from exc

    refresh_record = get_refresh_token(connection, refresh_payload.jti)
    expected_hash = hash_token(refresh_token, settings)
    if (
        refresh_record is None
        or refresh_record.revoked_at is not None
        or refresh_record.expires_at < datetime.now(UTC)
        or not secrets.compare_digest(refresh_record.token_hash, expected_hash)
    ):
        log_security_event(
            "refresh_token_rejected",
            request=request,
            user_id=str(refresh_payload.user_id),
            jti=refresh_payload.jti,
        )
        raise _invalid_credentials()

    user = get_user_by_id(connection, refresh_record.user_id)
    if user is None:
        log_security_event(
            "refresh_token_user_missing",
            request=request,
            user_id=str(refresh_payload.user_id),
            jti=refresh_payload.jti,
        )
        raise _invalid_credentials()

    token_response, new_refresh_jti = _issue_session(
        connection=connection,
        request=request,
        response=response,
        user=user,
        settings=settings,
    )
    revoke_refresh_token(
        connection,
        jti=refresh_payload.jti,
        replaced_by_jti=new_refresh_jti,
    )
    log_security_event(
        "refresh_token_rotated",
        request=request,
        user_id=str(user.id),
        jti=refresh_payload.jti,
    )
    return token_response


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT, summary="Log out")
def logout_user(
    request: Request,
    response: Response,
    connection: Annotated[sqlite3.Connection, Depends(get_connection)],
    settings: Annotated[Settings, Depends(get_settings)],
    _csrf_verified: Annotated[None, Depends(verify_csrf)],
) -> None:
    access_token = _extract_request_access_token(request, settings)
    if access_token is not None:
        try:
            access_payload = decode_access_token(access_token, settings)
            revoke_access_token(
                connection,
                jti=access_payload.jti,
                user_id=access_payload.user_id,
                expires_at=access_payload.expires_at,
            )
        except AuthTokenError:
            log_security_event("logout_access_token_invalid", request=request)

    refresh_token = request.cookies.get(settings.refresh_token_cookie_name)
    if refresh_token is not None:
        try:
            refresh_payload = decode_refresh_token(refresh_token, settings)
            revoke_refresh_token(connection, jti=refresh_payload.jti)
        except AuthTokenError:
            log_security_event("logout_refresh_token_invalid", request=request)

    _clear_auth_cookies(response, settings)


@router.get("/users/me", response_model=UserPublic, summary="Get current user")
def get_me(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    return current_user


@router.get(
    "/users/me/profile",
    response_model=UserProfilePublic,
    summary="Get current user's food profile",
)
def get_my_profile(
    current_user: Annotated[User, Depends(get_current_user)],
    connection: Annotated[sqlite3.Connection, Depends(get_connection)],
) -> UserProfile:
    return get_user_profile(connection, current_user.id)


@router.put(
    "/users/me/profile",
    response_model=UserProfilePublic,
    summary="Update current user's food profile",
)
def update_my_profile(
    payload: UserProfileUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    connection: Annotated[sqlite3.Connection, Depends(get_connection)],
    _csrf_verified: Annotated[None, Depends(verify_csrf)],
) -> UserProfile:
    return upsert_user_profile(
        connection,
        user_id=current_user.id,
        avoidances=payload.avoidances,
        allergies=payload.allergies,
        notes=payload.notes,
    )


@router.get(
    "/users/me/orders",
    response_model=list[OrderHistoryPublic],
    summary="List current user's order history",
)
def list_my_order_history(
    current_user: Annotated[User, Depends(get_current_user)],
    connection: Annotated[sqlite3.Connection, Depends(get_connection)],
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
) -> list[OrderHistory]:
    return list_order_history(connection, user_id=current_user.id, limit=limit)


@router.post(
    "/users/me/orders",
    response_model=OrderHistoryPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Create current user's order history entry",
)
def create_my_order_history(
    payload: OrderHistoryCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    connection: Annotated[sqlite3.Connection, Depends(get_connection)],
    _csrf_verified: Annotated[None, Depends(verify_csrf)],
) -> OrderHistory:
    return create_order_history(
        connection,
        user_id=current_user.id,
        restaurant_name=payload.restaurant_name,
        target_language=payload.target_language,
        customer_remark=payload.customer_remark,
        total_label=payload.total_label,
        total_amount=payload.total_amount,
        items=payload.items,
        generated_order=payload.generated_order,
    )


@router.get(
    "/users/me/dashboard",
    response_model=UserDashboardResponse,
    summary="Get current user's food profile dashboard",
)
def get_my_dashboard(
    current_user: Annotated[User, Depends(get_current_user)],
    connection: Annotated[sqlite3.Connection, Depends(get_connection)],
) -> UserDashboardResponse:
    profile = get_user_profile(connection, current_user.id)
    recent_orders = list_order_history(connection, user_id=current_user.id, limit=5)
    order_count = count_order_history(connection, current_user.id)
    latest_order_at = recent_orders[0].created_at if recent_orders else None
    updated_at = _latest_datetime(profile.updated_at, latest_order_at)

    return UserDashboardResponse(
        profile=UserProfilePublic.model_validate(profile),
        recent_orders=[OrderHistoryPublic.model_validate(order) for order in recent_orders],
        stats=UserDashboardStats(
            avoid_count=len(profile.avoidances),
            allergy_count=len(profile.allergies),
            order_count=order_count,
            updated_at=updated_at,
        ),
    )


def _latest_datetime(*values: datetime | None) -> datetime | None:
    available = [value for value in values if value is not None]
    return max(available) if available else None


def _username_conflict() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Username already exists",
    )


def _invalid_credentials() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _issue_session(
    *,
    connection: sqlite3.Connection,
    request: Request,
    response: Response,
    user: User,
    settings: Settings,
) -> tuple[TokenResponse, str]:
    access_token = create_access_token(user.id, settings)
    refresh_token = create_refresh_token(user.id, settings)
    store_refresh_token(
        connection,
        jti=refresh_token.payload.jti,
        user_id=user.id,
        token_hash=hash_token(refresh_token.token, settings),
        expires_at=refresh_token.payload.expires_at,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )

    csrf_token = generate_csrf_token()
    _set_auth_cookies(
        response=response,
        settings=settings,
        access_token=access_token.token,
        access_max_age=access_token.expires_in,
        refresh_token=refresh_token.token,
        refresh_max_age=refresh_token.expires_in,
    )
    _set_csrf_cookie(response, settings, csrf_token)
    return (
        TokenResponse(
            access_token=access_token.token,
            expires_in=access_token.expires_in,
            refresh_expires_in=refresh_token.expires_in,
            csrf_token=csrf_token,
            user=UserPublic.model_validate(user),
        ),
        refresh_token.payload.jti,
    )


def _set_auth_cookies(
    *,
    response: Response,
    settings: Settings,
    access_token: str,
    access_max_age: int,
    refresh_token: str,
    refresh_max_age: int,
) -> None:
    response.set_cookie(
        settings.access_token_cookie_name,
        access_token,
        max_age=access_max_age,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite=_cookie_samesite(settings),
        path="/",
    )
    response.set_cookie(
        settings.refresh_token_cookie_name,
        refresh_token,
        max_age=refresh_max_age,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite=_cookie_samesite(settings),
        path="/",
    )


def _set_csrf_cookie(response: Response, settings: Settings, csrf_token: str) -> None:
    response.set_cookie(
        settings.csrf_cookie_name,
        csrf_token,
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        httponly=False,
        secure=settings.auth_cookie_secure,
        samesite=_cookie_samesite(settings),
        path="/",
    )


def _clear_auth_cookies(response: Response, settings: Settings) -> None:
    for cookie_name in (
        settings.access_token_cookie_name,
        settings.refresh_token_cookie_name,
        settings.csrf_cookie_name,
    ):
        response.delete_cookie(
            cookie_name,
            secure=settings.auth_cookie_secure,
            samesite=_cookie_samesite(settings),
            path="/",
        )


def _extract_request_access_token(request: Request, settings: Settings) -> str | None:
    authorization = request.headers.get("authorization")
    if authorization is not None:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() == "bearer" and token:
            return token.strip()

    return request.cookies.get(settings.access_token_cookie_name)


def _rate_limit_key(request: Request, username: str) -> str:
    client_ip = request.client.host if request.client else "unknown"
    return f"{client_ip}:{username.lower()}"


def _cookie_samesite(settings: Settings) -> CookieSameSite:
    value = settings.auth_cookie_samesite.lower()
    if value in {"lax", "strict", "none"}:
        return cast(CookieSameSite, value)
    return "strict"
