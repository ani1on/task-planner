from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .tag import TagResponse

TaskStatus = Literal["todo", "in_progress", "review", "done"]

TaskPriority = Literal["low", "medium", "high", "critical"]


class TaskCreate(BaseModel):
    project_id: int
    title: str = Field(min_length=1, max_length=500)
    description: str | None = None
    status: TaskStatus = "todo"
    priority: TaskPriority = "medium"
    parent_task_id: int | None = None
    assignee_id: int | None = None
    start_at: datetime | None = None
    due_at: datetime | None = None
    position: int = 0


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    parent_task_id: int | None = None
    assignee_id: int | None = None
    start_at: datetime | None = None
    due_at: datetime | None = None
    position: int | None = None


class SubtaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    description: str | None = None
    status: TaskStatus = "todo"
    priority: TaskPriority = "medium"
    assignee_id: int | None = None
    start_at: datetime | None = None
    due_at: datetime | None = None
    position: int = 0


class SubtaskProgress(BaseModel):
    total: int
    completed: int


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    parent_task_id: int | None
    assignee_id: int | None
    created_by_id: int
    title: str
    description: str | None
    status: str
    priority: str
    position: int
    start_at: datetime | None
    due_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    tags: list[TagResponse] = []
