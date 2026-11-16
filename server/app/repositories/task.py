from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from ..models.task import Task
from ..models.task_tag import TaskTag
from .base import BaseRepository
from .project import accessible_project_ids


class TaskRepository(BaseRepository[Task]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Task)

    @staticmethod
    def _with_tags(statement):
        return statement.options(
            selectinload(Task.task_tags).selectinload(TaskTag.tag),
        )

    def list_for_user(
        self,
        user_id: int,
        project_id: int | None = None,
        status: str | None = None,
        priority: str | None = None,
        assignee_id: int | None = None,
        tag_id: int | None = None,
        search: str | None = None,
    ) -> list[Task]:
        statement = self._with_tags(
            select(Task).where(
                Task.project_id.in_(accessible_project_ids(user_id)),
                Task.deleted_at.is_(None),
            )
        )

        if project_id is not None:
            statement = statement.where(Task.project_id == project_id)

        if status is not None:
            statement = statement.where(Task.status == status)

        if priority is not None:
            statement = statement.where(Task.priority == priority)

        if assignee_id is not None:
            statement = statement.where(Task.assignee_id == assignee_id)

        if tag_id is not None:
            statement = statement.join(
                TaskTag,
                TaskTag.task_id == Task.id,
            ).where(TaskTag.tag_id == tag_id)

        if search:
            pattern = f"%{search}%"

            statement = statement.where(
                or_(
                    Task.title.ilike(pattern),
                    Task.description.ilike(pattern),
                )
            )

        statement = statement.order_by(
            Task.position.asc(),
            Task.created_at.desc(),
        )

        return list(self.db.scalars(statement).all())

    def list_subtasks(
        self,
        parent_task_id: int,
    ) -> list[Task]:
        statement = self._with_tags(
            select(Task)
            .where(
                Task.parent_task_id == parent_task_id,
                Task.deleted_at.is_(None),
            )
            .order_by(
                Task.position.asc(),
                Task.created_at.desc(),
            )
        )

        return list(self.db.scalars(statement).all())

    def get_for_user(
        self,
        task_id: int,
        user_id: int,
    ) -> Task | None:
        statement = self._with_tags(
            select(Task).where(
                Task.id == task_id,
                Task.project_id.in_(accessible_project_ids(user_id)),
                Task.deleted_at.is_(None),
            )
        )

        return self.db.scalar(statement)

    def search(
        self,
        user_id: int,
        query: str,
        limit: int = 20,
    ) -> list[Task]:
        pattern = f"%{query}%"

        statement = self._with_tags(
            select(Task)
            .where(
                Task.project_id.in_(accessible_project_ids(user_id)),
                Task.deleted_at.is_(None),
                or_(
                    Task.title.ilike(pattern),
                    Task.description.ilike(pattern),
                ),
            )
            .order_by(Task.updated_at.desc())
            .limit(limit)
        )

        return list(self.db.scalars(statement).all())
