from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class User:
    id: UUID
    username: str
    nickname: str
    avatar_url: str | None
    password_salt: str
    password_hash: str
    created_at: datetime
    updated_at: datetime
