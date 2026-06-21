from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

ProfileLabel = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=80),
]


class UserProfileUpdate(BaseModel):
    avoidances: list[ProfileLabel] = Field(default_factory=list, max_length=50)
    allergies: list[ProfileLabel] = Field(default_factory=list, max_length=50)
    notes: str = Field(default="", max_length=1000)

    @field_validator("notes")
    @classmethod
    def strip_notes(cls, value: str) -> str:
        return value.strip()


class UserProfilePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    avoidances: list[str]
    allergies: list[str]
    notes: str
    updated_at: datetime | None


class OrderHistoryCreate(BaseModel):
    restaurant_name: str | None = Field(default=None, max_length=120)
    target_language: str | None = Field(default=None, max_length=40)
    customer_remark: str = Field(default="", max_length=1000)
    total_label: str = Field(min_length=1, max_length=80)
    total_amount: float | None = Field(default=None, ge=0)
    items: list[dict[str, Any]] = Field(min_length=1, max_length=100)
    generated_order: dict[str, Any] | None = None

    @field_validator("restaurant_name", "target_language")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None

        stripped = value.strip()
        return stripped or None

    @field_validator("customer_remark")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("total_label")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            msg = "Field must not be blank."
            raise ValueError(msg)

        return stripped


class OrderHistoryPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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


class UserDashboardStats(BaseModel):
    avoid_count: int
    allergy_count: int
    order_count: int
    updated_at: datetime | None


class UserDashboardResponse(BaseModel):
    profile: UserProfilePublic
    recent_orders: list[OrderHistoryPublic]
    stats: UserDashboardStats
