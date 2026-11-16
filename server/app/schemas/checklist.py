from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ChecklistCreate(BaseModel):
    task_id: int
    title: str = Field(min_length=1, max_length=255)
    position: int = 0


class ChecklistUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    position: int | None = None


class ChecklistResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    title: str
    position: int
    created_at: datetime
    updated_at: datetime


class ChecklistItemCreate(BaseModel):
    content: str = Field(min_length=1, max_length=500)
    position: int = 0


class ChecklistItemUpdate(BaseModel):
    content: str | None = Field(default=None, min_length=1, max_length=500)
    is_completed: bool | None = None
    position: int | None = None


class ChecklistItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    checklist_id: int
    content: str
    is_completed: bool
    position: int
    created_at: datetime
    updated_at: datetime
