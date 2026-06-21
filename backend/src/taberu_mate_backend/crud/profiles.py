import json
import sqlite3
from datetime import UTC, datetime
from typing import Any, cast
from uuid import UUID, uuid4

from taberu_mate_backend.models.profile import OrderHistory, UserProfile


def get_user_profile(connection: sqlite3.Connection, user_id: UUID) -> UserProfile:
    row = connection.execute(
        """
        SELECT user_id, avoidances_json, allergies_json, notes, updated_at
        FROM user_profiles
        WHERE user_id = ?
        LIMIT 1
        """,
        (str(user_id),),
    ).fetchone()

    if row is None:
        return UserProfile(
            user_id=user_id,
            avoidances=[],
            allergies=[],
            notes="",
            updated_at=None,
        )

    return _row_to_profile(row)


def upsert_user_profile(
    connection: sqlite3.Connection,
    *,
    user_id: UUID,
    avoidances: list[str],
    allergies: list[str],
    notes: str,
) -> UserProfile:
    now = datetime.now(UTC)
    connection.execute(
        """
        INSERT INTO user_profiles (
            user_id, avoidances_json, allergies_json, notes, updated_at
        )
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            avoidances_json = excluded.avoidances_json,
            allergies_json = excluded.allergies_json,
            notes = excluded.notes,
            updated_at = excluded.updated_at
        """,
        (
            str(user_id),
            _dump_json(avoidances),
            _dump_json(allergies),
            notes,
            now.isoformat(),
        ),
    )
    connection.commit()
    return UserProfile(
        user_id=user_id,
        avoidances=avoidances,
        allergies=allergies,
        notes=notes,
        updated_at=now,
    )


def create_order_history(
    connection: sqlite3.Connection,
    *,
    user_id: UUID,
    restaurant_name: str | None,
    target_language: str | None,
    customer_remark: str,
    total_label: str,
    total_amount: float | None,
    items: list[dict[str, Any]],
    generated_order: dict[str, Any] | None,
) -> OrderHistory:
    now = datetime.now(UTC)
    order = OrderHistory(
        id=uuid4(),
        user_id=user_id,
        restaurant_name=restaurant_name,
        target_language=target_language,
        customer_remark=customer_remark,
        total_label=total_label,
        total_amount=total_amount,
        items=items,
        generated_order=generated_order,
        created_at=now,
    )
    connection.execute(
        """
        INSERT INTO order_history (
            id, user_id, restaurant_name, target_language, customer_remark,
            total_label, total_amount, items_json, generated_order_json, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            str(order.id),
            str(order.user_id),
            order.restaurant_name,
            order.target_language,
            order.customer_remark,
            order.total_label,
            order.total_amount,
            _dump_json(order.items),
            _dump_json(order.generated_order) if order.generated_order is not None else None,
            order.created_at.isoformat(),
        ),
    )
    connection.commit()
    return order


def list_order_history(
    connection: sqlite3.Connection,
    *,
    user_id: UUID,
    limit: int = 20,
) -> list[OrderHistory]:
    rows = connection.execute(
        """
        SELECT
            id, user_id, restaurant_name, target_language, customer_remark,
            total_label, total_amount, items_json, generated_order_json, created_at
        FROM order_history
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (str(user_id), limit),
    ).fetchall()
    return [_row_to_order(row) for row in rows]


def count_order_history(connection: sqlite3.Connection, user_id: UUID) -> int:
    row = connection.execute(
        """
        SELECT count(*) AS order_count
        FROM order_history
        WHERE user_id = ?
        """,
        (str(user_id),),
    ).fetchone()
    return int(row["order_count"]) if row is not None else 0


def _row_to_profile(row: sqlite3.Row) -> UserProfile:
    return UserProfile(
        user_id=UUID(cast(str, row["user_id"])),
        avoidances=_json_list(cast(str, row["avoidances_json"])),
        allergies=_json_list(cast(str, row["allergies_json"])),
        notes=cast(str, row["notes"]),
        updated_at=datetime.fromisoformat(cast(str, row["updated_at"])),
    )


def _row_to_order(row: sqlite3.Row) -> OrderHistory:
    generated_order_raw = cast(str | None, row["generated_order_json"])
    return OrderHistory(
        id=UUID(cast(str, row["id"])),
        user_id=UUID(cast(str, row["user_id"])),
        restaurant_name=cast(str | None, row["restaurant_name"]),
        target_language=cast(str | None, row["target_language"]),
        customer_remark=cast(str, row["customer_remark"]),
        total_label=cast(str, row["total_label"]),
        total_amount=cast(float | None, row["total_amount"]),
        items=_json_items(cast(str, row["items_json"])),
        generated_order=_json_object(generated_order_raw) if generated_order_raw else None,
        created_at=datetime.fromisoformat(cast(str, row["created_at"])),
    )


def _json_list(raw: str) -> list[str]:
    data = _load_json(raw)
    if not isinstance(data, list):
        return []

    return [item.strip() for item in data if isinstance(item, str) and item.strip()]


def _json_items(raw: str) -> list[dict[str, Any]]:
    data = _load_json(raw)
    if not isinstance(data, list):
        return []

    return [dict(item) for item in data if isinstance(item, dict)]


def _json_object(raw: str) -> dict[str, Any] | None:
    data = _load_json(raw)
    if not isinstance(data, dict):
        return None

    return dict(data)


def _load_json(raw: str) -> Any:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def _dump_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
