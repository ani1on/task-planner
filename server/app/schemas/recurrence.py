from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Frequency = Literal["daily", "weekly", "monthly"]


def _validate_days_of_week(
    value: list[int] | None,
) -> list[int] | None:
    if value is None:
        return None

    if not value:
        raise ValueError("days_of_week must not be empty")

    if any(day < 1 or day > 7 for day in value):
        raise ValueError("days_of_week values must be between 1 and 7")

    return sorted(set(value))


class RecurrenceBase(BaseModel):
    frequency: Frequency
    interval: int = Field(default=1, ge=1, le=365)
    days_of_week: list[int] | None = None
    day_of_month: int | None = Field(default=None, ge=1, le=31)
    start_at: datetime
    end_at: datetime | None = None
    is_active: bool = True

    @field_validator("days_of_week")
    @classmethod
    def validate_days_of_week(
        cls,
        value: list[int] | None,
    ) -> list[int] | None:
        return _validate_days_of_week(value)


class RecurrenceCreate(RecurrenceBase):
    pass


class RecurrenceUpdate(BaseModel):
    frequency: Frequency | None = None
    interval: int | None = Field(default=None, ge=1, le=365)
    days_of_week: list[int] | None = None
    day_of_month: int | None = Field(default=None, ge=1, le=31)
    start_at: datetime | None = None
    end_at: datetime | None = None
    is_active: bool | None = None

    @field_validator("days_of_week")
    @classmethod
    def validate_days_of_week(
        cls,
        value: list[int] | None,
    ) -> list[int] | None:
        return _validate_days_of_week(value)


class RecurrenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    frequency: str
    interval: int
    days_of_week: list[int] | None
    day_of_month: int | None
    start_at: datetime
    end_at: datetime | None
    next_run_at: datetime | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
