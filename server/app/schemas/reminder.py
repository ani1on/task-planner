from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ReminderChannel = Literal["desktop", "email", "in_app"]
ReminderStatus = Literal["pending", "sent", "cancelled"]


class ReminderCreate(BaseModel):
    task_id: int | None = None
    event_id: int | None = None
    remind_at: datetime
    channel: ReminderChannel = "desktop"


class ReminderUpdate(BaseModel):
    remind_at: datetime | None = None
    channel: ReminderChannel | None = None
    status: ReminderStatus | None = None


class ReminderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    task_id: int | None
    event_id: int | None
    remind_at: datetime
    channel: str
    status: str
    sent_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ReminderProcessResponse(BaseModel):
    processed: int = Field(ge=0)
