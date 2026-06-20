from time import monotonic

_attempts: dict[str, list[float]] = {}


def is_rate_limited(*, key: str, limit: int, window_seconds: int) -> bool:
    now = monotonic()
    window_started_at = now - window_seconds
    recent_attempts = [
        attempt for attempt in _attempts.get(key, []) if attempt >= window_started_at
    ]

    if len(recent_attempts) >= limit:
        _attempts[key] = recent_attempts
        return True

    recent_attempts.append(now)
    _attempts[key] = recent_attempts
    return False


def reset_rate_limit(*, key: str) -> None:
    _attempts.pop(key, None)
