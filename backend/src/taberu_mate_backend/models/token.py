from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class RefreshTokenRecord:
    jti: str
    user_id: UUID
    token_hash: str
    expires_at: datetime
    revoked_at: datetime | None
    replaced_by_jti: str | None
    created_at: datetime
    updated_at: datetime
    user_agent: str | None
    ip_address: str | None
