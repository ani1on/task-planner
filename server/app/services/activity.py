from typing import Any

from sqlalchemy.orm import Session

from ..core.serialization import jsonable
from ..models.activity_log import ActivityLog
from ..repositories.activity_log import ActivityLogRepository


class ActivityService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.activity = ActivityLogRepository(db)

    def log(
        self,
        *,
        user_id: int | None,
        action: str,
        entity_type: str,
        entity_id: int,
        project_id: int | None = None,
        task_id: int | None = None,
        old_values: dict[str, Any] | None = None,
        new_values: dict[str, Any] | None = None,
    ) -> ActivityLog:
        entry = ActivityLog(
            user_id=user_id,
            project_id=project_id,
            task_id=task_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_values=jsonable(old_values) if old_values is not None else None,
            new_values=jsonable(new_values) if new_values is not None else None,
        )

        return self.activity.create(entry)

    def list(
        self,
        user_id: int,
        project_id: int | None = None,
        task_id: int | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ActivityLog]:
        return self.activity.list_for_user(
            user_id=user_id,
            project_id=project_id,
            task_id=task_id,
            limit=limit,
            offset=offset,
        )
