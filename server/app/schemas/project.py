from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5555)
    color: str = Field(default="blue", max_length=20)


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5555)
    color: str | None = Field(default=None, max_length=20)
    status: Literal["active", "archived"] | None = None


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    name: str
    description: str | None
    color: str
    status: str
    role: str | None = None
    progress: int = 0
    tasks_total: int = 0
    tasks_done: int = 0
    created_at: datetime
    updated_at: datetime
