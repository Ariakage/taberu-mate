import json
import logging
from typing import Any

from fastapi import Request

security_logger = logging.getLogger("taberu_mate.security")


def log_security_event(
    event: str,
    *,
    request: Request | None = None,
    reason: str | None = None,
    username: str | None = None,
    user_id: str | None = None,
    jti: str | None = None,
) -> None:
    payload: dict[str, Any] = {"event": event}
    if reason is not None:
        payload["reason"] = reason
    if username is not None:
        payload["username"] = username
    if user_id is not None:
        payload["user_id"] = user_id
    if jti is not None:
        payload["jti"] = jti
    if request is not None:
        payload["method"] = request.method
        payload["path"] = request.url.path
        payload["client_ip"] = request.client.host if request.client else None
        payload["user_agent"] = request.headers.get("user-agent")

    security_logger.warning(json.dumps(payload, ensure_ascii=False, sort_keys=True))
