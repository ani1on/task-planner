from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class ActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None
    project_id: int | None
    task_id: int | None
    action: str
    entity_type: str
    entity_id: int
    old_values: dict[str, Any] | None
    new_values: dict[str, Any] | None
    created_at: datetime
