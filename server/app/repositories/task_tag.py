from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.tag import Tag
from ..models.task_tag import TaskTag
from .base import BaseRepository


class TaskTagRepository(BaseRepository[TaskTag]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, TaskTag)

    def get(
        self,
        task_id: int,
        tag_id: int,
    ) -> TaskTag | None:
        statement = select(TaskTag).where(
            TaskTag.task_id == task_id,
            TaskTag.tag_id == tag_id,
        )

        return self.db.scalar(statement)

    def list_tags_for_task(
        self,
        task_id: int,
    ) -> list[Tag]:
        statement = (
            select(Tag)
            .join(TaskTag, TaskTag.tag_id == Tag.id)
            .where(TaskTag.task_id == task_id)
            .order_by(Tag.name.asc())
        )

        return list(self.db.scalars(statement).all())
