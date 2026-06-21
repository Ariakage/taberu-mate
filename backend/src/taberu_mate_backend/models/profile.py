from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(frozen=True, slots=True)
class UserProfile:
    user_id: UUID
    avoidances: list[str]
    allergies: list[str]
    notes: str
    updated_at: datetime | None


@dataclass(frozen=True, slots=True)
class OrderHistory:
    id: UUID
    user_id: UUID
    restaurant_name: str | None
    target_language: str | None
    customer_remark: str
    total_label: str
    total_amount: float | None
    items: list[dict[str, Any]]
    generated_order: dict[str, Any] | None
    created_at: datetime
