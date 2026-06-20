import base64
import binascii
import hashlib
import hmac
import json
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Literal
from uuid import UUID, uuid4

from argon2.exceptions import VerificationError
from argon2.low_level import Type, hash_secret, verify_secret

from taberu_mate_backend.core.config import Settings

TokenType = Literal["access", "refresh"]
ARGON2_TIME_COST = 2
ARGON2_MEMORY_COST = 19 * 1024
ARGON2_PARALLELISM = 1
ARGON2_HASH_LEN = 32
ARGON2_SALT_LEN = 16


class AuthTokenError(ValueError):
    pass


class CsrfTokenError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class TokenPayload:
    user_id: UUID
    jti: str
    token_type: TokenType
    issued_at: datetime
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class IssuedToken:
    token: str
    payload: TokenPayload
    expires_in: int


@dataclass(frozen=True, slots=True)
class PasswordHash:
    salt: str
    password_hash: str


def hash_password(password: str) -> PasswordHash:
    salt = secrets.token_bytes(ARGON2_SALT_LEN)
    password_hash = hash_secret(
        password.encode("utf-8"),
        salt,
        time_cost=ARGON2_TIME_COST,
        memory_cost=ARGON2_MEMORY_COST,
        parallelism=ARGON2_PARALLELISM,
        hash_len=ARGON2_HASH_LEN,
        type=Type.ID,
    ).decode("utf-8")
    return PasswordHash(salt=_extract_argon2_salt(password_hash), password_hash=password_hash)


def verify_password(
    password: str,
    password_salt: str,
    expected_hash: str,
) -> bool:
    return _verify_argon2id_password(password, password_salt, expected_hash)


def create_access_token(user_id: UUID, settings: Settings) -> IssuedToken:
    return _create_jwt(
        user_id=user_id,
        token_type="access",
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        settings=settings,
    )


def create_refresh_token(user_id: UUID, settings: Settings) -> IssuedToken:
    return _create_jwt(
        user_id=user_id,
        token_type="refresh",
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
        settings=settings,
    )


def decode_access_token(token: str, settings: Settings) -> TokenPayload:
    return decode_token(token, expected_type="access", settings=settings)


def decode_refresh_token(token: str, settings: Settings) -> TokenPayload:
    return decode_token(token, expected_type="refresh", settings=settings)


def decode_token(token: str, *, expected_type: TokenType, settings: Settings) -> TokenPayload:
    header_part, payload_part, signature_part = _split_token(token)
    signing_input = f"{header_part}.{payload_part}"
    expected_signature = _sign(signing_input, settings.auth_token_secret)

    if not secrets.compare_digest(signature_part, expected_signature):
        raise AuthTokenError

    header = _decode_json(header_part)
    if header.get("alg") != "HS256" or header.get("typ") != "JWT":
        raise AuthTokenError

    payload = _decode_payload(payload_part)
    expires_at = payload.get("exp")
    issued_at = payload.get("iat")
    subject = payload.get("sub")
    token_type = payload.get("typ")
    jti = payload.get("jti")

    if not isinstance(expires_at, int) or expires_at < int(datetime.now(UTC).timestamp()):
        raise AuthTokenError

    if not isinstance(issued_at, int):
        raise AuthTokenError

    if token_type != expected_type:
        raise AuthTokenError

    if not isinstance(subject, str) or not isinstance(jti, str) or not jti:
        raise AuthTokenError

    try:
        user_id = UUID(subject)
    except ValueError as exc:
        raise AuthTokenError from exc

    return TokenPayload(
        user_id=user_id,
        jti=jti,
        token_type=expected_type,
        issued_at=datetime.fromtimestamp(issued_at, UTC),
        expires_at=datetime.fromtimestamp(expires_at, UTC),
    )


def hash_token(token: str, settings: Settings) -> str:
    return hmac.new(
        settings.auth_token_secret.encode("utf-8"),
        token.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def verify_csrf_token(cookie_token: str | None, header_token: str | None) -> None:
    if not cookie_token or not header_token:
        raise CsrfTokenError

    if not secrets.compare_digest(cookie_token, header_token):
        raise CsrfTokenError


def _verify_argon2id_password(
    password: str,
    password_salt: str,
    expected_hash: str,
) -> bool:
    if not _is_argon2id_hash(expected_hash):
        return False

    try:
        if _extract_argon2_salt(expected_hash) != password_salt:
            return False
        return verify_secret(expected_hash.encode("utf-8"), password.encode("utf-8"), Type.ID)
    except (ValueError, VerificationError):
        return False


def _is_argon2id_hash(password_hash: str) -> bool:
    return password_hash.startswith("$argon2id$")


def _extract_argon2_salt(password_hash: str) -> str:
    parts = password_hash.split("$")
    if len(parts) < 5 or parts[1] != "argon2id":
        msg = "Invalid Argon2id password hash"
        raise ValueError(msg)

    return parts[4]


def _create_jwt(
    *,
    user_id: UUID,
    token_type: TokenType,
    expires_delta: timedelta,
    settings: Settings,
) -> IssuedToken:
    issued_at = datetime.now(UTC)
    expires_at = issued_at + expires_delta
    payload = TokenPayload(
        user_id=user_id,
        jti=str(uuid4()),
        token_type=token_type,
        issued_at=issued_at,
        expires_at=expires_at,
    )
    header_part = _base64url_encode(
        json.dumps(
            {"alg": "HS256", "typ": "JWT"},
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    )
    payload_part = _base64url_encode(
        json.dumps(
            {
                "exp": int(payload.expires_at.timestamp()),
                "iat": int(payload.issued_at.timestamp()),
                "jti": payload.jti,
                "sub": str(payload.user_id),
                "typ": payload.token_type,
            },
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    )
    signing_input = f"{header_part}.{payload_part}"
    signature_part = _sign(signing_input, settings.auth_token_secret)
    return IssuedToken(
        token=f"{signing_input}.{signature_part}",
        payload=payload,
        expires_in=int(expires_delta.total_seconds()),
    )


def _split_token(token: str) -> tuple[str, str, str]:
    parts = token.split(".")
    if len(parts) != 3:
        raise AuthTokenError

    header_part, payload_part, signature_part = parts
    if not header_part or not payload_part or not signature_part:
        raise AuthTokenError

    return header_part, payload_part, signature_part


def _decode_payload(payload_part: str) -> dict[str, Any]:
    payload = _decode_json(payload_part)
    if not isinstance(payload, dict):
        raise AuthTokenError

    return payload


def _decode_json(value: str) -> dict[str, Any]:
    try:
        payload = json.loads(_base64url_decode(value))
    except (binascii.Error, ValueError, json.JSONDecodeError) as exc:
        raise AuthTokenError from exc

    if not isinstance(payload, dict):
        raise AuthTokenError

    return payload


def _sign(value: str, secret: str) -> str:
    signature = hmac.new(secret.encode("utf-8"), value.encode("ascii"), hashlib.sha256).digest()
    return _base64url_encode(signature)


def _base64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _base64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}".encode("ascii"))
