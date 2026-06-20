import sqlite3
from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends

from taberu_mate_backend.core.config import Settings, get_settings


def connect(settings: Settings) -> sqlite3.Connection:
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(settings.database_path, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db(settings: Settings) -> None:
    with connect(settings) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT NOT NULL CHECK(length(username) BETWEEN 3 AND 32),
                nickname TEXT NOT NULL CHECK(length(nickname) BETWEEN 1 AND 50),
                avatar_url TEXT,
                password_salt TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        _ensure_users_nickname_column(connection)
        _ensure_users_password_salt_column(connection)
        connection.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username_lower
            ON users (lower(username))
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS refresh_tokens (
                jti TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                token_hash TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                revoked_at TEXT,
                replaced_by_jti TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                user_agent TEXT,
                ip_address TEXT
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id
            ON refresh_tokens (user_id)
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS access_token_revocations (
                jti TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                expires_at TEXT NOT NULL,
                revoked_at TEXT NOT NULL
            )
            """
        )
        connection.commit()


def get_connection(
    settings: Annotated[Settings, Depends(get_settings)],
) -> Iterator[sqlite3.Connection]:
    connection = connect(settings)
    try:
        yield connection
    finally:
        connection.close()


def _ensure_users_nickname_column(connection: sqlite3.Connection) -> None:
    columns = _users_columns(connection)
    if "nickname" in columns:
        return

    connection.execute(
        """
        ALTER TABLE users
        ADD COLUMN nickname TEXT
        """
    )
    connection.execute(
        """
        UPDATE users
        SET nickname = username
        WHERE nickname IS NULL OR length(nickname) = 0
        """
    )


def _ensure_users_password_salt_column(connection: sqlite3.Connection) -> None:
    columns = _users_columns(connection)
    if "password_salt" in columns:
        return

    connection.execute(
        """
        ALTER TABLE users
        ADD COLUMN password_salt TEXT
        """
    )


def _users_columns(connection: sqlite3.Connection) -> set[str]:
    return {
        row["name"]
        for row in connection.execute(
            """
            PRAGMA table_info(users)
            """
        ).fetchall()
    }
