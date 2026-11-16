from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..models.activity_log import ActivityLog
from .base import BaseRepository
from .project import accessible_project_ids


class ActivityLogRepository(BaseRepository[ActivityLog]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, ActivityLog)

    def list_for_user(
        self,
        user_id: int,
        project_id: int | None = None,
        task_id: int | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ActivityLog]:
        statement = select(ActivityLog).where(
            or_(
                ActivityLog.project_id.in_(accessible_project_ids(user_id)),
                ActivityLog.user_id == user_id,
            )
        )

        if project_id is not None:
            statement = statement.where(ActivityLog.project_id == project_id)

        if task_id is not None:
            statement = statement.where(ActivityLog.task_id == task_id)

        statement = (
            statement.order_by(ActivityLog.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        return list(self.db.scalars(statement).all())
