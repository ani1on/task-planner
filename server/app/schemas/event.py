from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class EventCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    start_at: datetime
    end_at: datetime
    description: str | None = None
    project_id: int | None = None
    task_id: int | None = None
    all_day: bool = False
    location: str | None = Field(default=None, max_length=500)


class EventUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    start_at: datetime | None = None
    end_at: datetime | None = None
    description: str | None = None
    project_id: int | None = None
    task_id: int | None = None
    all_day: bool | None = None
    location: str | None = Field(default=None, max_length=500)


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    project_id: int | None
    task_id: int | None
    title: str
    description: str | None
    start_at: datetime
    end_at: datetime
    all_day: bool
    location: str | None
    created_at: datetime
    updated_at: datetime
