import sqlite3
from datetime import UTC, datetime
from typing import cast
from uuid import UUID, uuid4

from taberu_mate_backend.models.user import User


def create_user(
    connection: sqlite3.Connection,
    *,
    username: str,
    nickname: str,
    avatar_url: str | None,
    password_salt: str,
    password_hash: str,
) -> User:
    now = datetime.now(UTC)
    user = User(
        id=uuid4(),
        username=username,
        nickname=nickname,
        avatar_url=avatar_url,
        password_salt=password_salt,
        password_hash=password_hash,
        created_at=now,
        updated_at=now,
    )
    connection.execute(
        """
        INSERT INTO users (
            id, username, nickname, avatar_url, password_salt, password_hash,
            created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            str(user.id),
            user.username,
            user.nickname,
            user.avatar_url,
            user.password_salt,
            user.password_hash,
            user.created_at.isoformat(),
            user.updated_at.isoformat(),
        ),
    )
    connection.commit()
    return user


def get_user_by_username(connection: sqlite3.Connection, username: str) -> User | None:
    row = connection.execute(
        """
        SELECT
            id, username, nickname, avatar_url, password_salt, password_hash,
            created_at, updated_at
        FROM users
        WHERE lower(username) = lower(?)
        LIMIT 1
        """,
        (username,),
    ).fetchone()
    return _row_to_user(row) if row else None


def get_user_by_id(connection: sqlite3.Connection, user_id: UUID) -> User | None:
    row = connection.execute(
        """
        SELECT
            id, username, nickname, avatar_url, password_salt, password_hash,
            created_at, updated_at
        FROM users
        WHERE id = ?
        LIMIT 1
        """,
        (str(user_id),),
    ).fetchone()
    return _row_to_user(row) if row else None


def _row_to_user(row: sqlite3.Row) -> User:
    return User(
        id=UUID(cast(str, row["id"])),
        username=cast(str, row["username"]),
        nickname=cast(str, row["nickname"]),
        avatar_url=cast(str | None, row["avatar_url"]),
        password_salt=cast(str, row["password_salt"]),
        password_hash=cast(str, row["password_hash"]),
        created_at=datetime.fromisoformat(cast(str, row["created_at"])),
        updated_at=datetime.fromisoformat(cast(str, row["updated_at"])),
    )
