from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, StringConstraints

Username = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=3,
        max_length=32,
        pattern=r"^[A-Za-z0-9_]+$",
    ),
]
Nickname = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]


class UserCreate(BaseModel):
    username: Username
    nickname: Nickname | None = None
    avatar_url: HttpUrl | None = None
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    username: Username
    password: str = Field(min_length=8, max_length=128)


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    nickname: str
    avatar_url: HttpUrl | None
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_expires_in: int
    csrf_token: str
    user: UserPublic


class CsrfTokenResponse(BaseModel):
    csrf_token: str
