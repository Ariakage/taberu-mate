import sqlite3
from datetime import UTC, datetime
from typing import cast
from uuid import UUID

from taberu_mate_backend.models.token import RefreshTokenRecord


def store_refresh_token(
    connection: sqlite3.Connection,
    *,
    jti: str,
    user_id: UUID,
    token_hash: str,
    expires_at: datetime,
    user_agent: str | None,
    ip_address: str | None,
) -> None:
    now = datetime.now(UTC)
    connection.execute(
        """
        INSERT INTO refresh_tokens (
            jti, user_id, token_hash, expires_at, revoked_at, replaced_by_jti,
            created_at, updated_at, user_agent, ip_address
        )
        VALUES (?, ?, ?, ?, NULL, NULL, ?, ?, ?, ?)
        """,
        (
            jti,
            str(user_id),
            token_hash,
            expires_at.isoformat(),
            now.isoformat(),
            now.isoformat(),
            user_agent,
            ip_address,
        ),
    )
    connection.commit()


def get_refresh_token(connection: sqlite3.Connection, jti: str) -> RefreshTokenRecord | None:
    row = connection.execute(
        """
        SELECT
            jti, user_id, token_hash, expires_at, revoked_at, replaced_by_jti,
            created_at, updated_at, user_agent, ip_address
        FROM refresh_tokens
        WHERE jti = ?
        LIMIT 1
        """,
        (jti,),
    ).fetchone()
    return _row_to_refresh_token(row) if row else None


def revoke_refresh_token(
    connection: sqlite3.Connection,
    *,
    jti: str,
    replaced_by_jti: str | None = None,
) -> None:
    now = datetime.now(UTC).isoformat()
    connection.execute(
        """
        UPDATE refresh_tokens
        SET revoked_at = COALESCE(revoked_at, ?),
            replaced_by_jti = COALESCE(replaced_by_jti, ?),
            updated_at = ?
        WHERE jti = ?
        """,
        (now, replaced_by_jti, now, jti),
    )
    connection.commit()


def is_access_token_revoked(connection: sqlite3.Connection, jti: str) -> bool:
    row = connection.execute(
        """
        SELECT 1
        FROM access_token_revocations
        WHERE jti = ?
        LIMIT 1
        """,
        (jti,),
    ).fetchone()
    return row is not None


def revoke_access_token(
    connection: sqlite3.Connection,
    *,
    jti: str,
    user_id: UUID,
    expires_at: datetime,
) -> None:
    connection.execute(
        """
        INSERT OR IGNORE INTO access_token_revocations (jti, user_id, expires_at, revoked_at)
        VALUES (?, ?, ?, ?)
        """,
        (
            jti,
            str(user_id),
            expires_at.isoformat(),
            datetime.now(UTC).isoformat(),
        ),
    )
    connection.commit()


def cleanup_expired_token_records(connection: sqlite3.Connection) -> None:
    now = datetime.now(UTC).isoformat()
    connection.execute(
        """
        DELETE FROM access_token_revocations
        WHERE expires_at < ?
        """,
        (now,),
    )
    connection.execute(
        """
        DELETE FROM refresh_tokens
        WHERE expires_at < ? AND revoked_at IS NOT NULL
        """,
        (now,),
    )
    connection.commit()


def _row_to_refresh_token(row: sqlite3.Row) -> RefreshTokenRecord:
    revoked_at = cast(str | None, row["revoked_at"])
    return RefreshTokenRecord(
        jti=cast(str, row["jti"]),
        user_id=UUID(cast(str, row["user_id"])),
        token_hash=cast(str, row["token_hash"]),
        expires_at=datetime.fromisoformat(cast(str, row["expires_at"])),
        revoked_at=datetime.fromisoformat(revoked_at) if revoked_at else None,
        replaced_by_jti=cast(str | None, row["replaced_by_jti"]),
        created_at=datetime.fromisoformat(cast(str, row["created_at"])),
        updated_at=datetime.fromisoformat(cast(str, row["updated_at"])),
        user_agent=cast(str | None, row["user_agent"]),
        ip_address=cast(str | None, row["ip_address"]),
    )
