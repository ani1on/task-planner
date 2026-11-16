from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.task_recurrence import TaskRecurrence
from .base import BaseRepository


class TaskRecurrenceRepository(BaseRepository[TaskRecurrence]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, TaskRecurrence)

    def get_for_task(
        self,
        task_id: int,
    ) -> TaskRecurrence | None:
        statement = select(TaskRecurrence).where(
            TaskRecurrence.task_id == task_id,
        )

        return self.db.scalar(statement)
