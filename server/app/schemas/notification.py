from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NotificationCreate(BaseModel):
    type: str = Field(min_length=1, max_length=50)
    title: str = Field(min_length=1, max_length=255)
    message: str = Field(min_length=1)
    task_id: int | None = None
    project_id: int | None = None


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    type: str
    title: str
    message: str
    task_id: int | None
    project_id: int | None
    is_read: bool
    read_at: datetime | None
    created_at: datetime


class UnreadCountResponse(BaseModel):
    count: int
