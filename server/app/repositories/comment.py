from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.comment import Comment
from ..models.task import Task
from .base import BaseRepository
from .project import accessible_project_ids


class CommentRepository(BaseRepository[Comment]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Comment)

    def list_for_user(
        self,
        user_id: int,
        task_id: int | None = None,
    ) -> list[Comment]:
        statement = (
            select(Comment)
            .join(Task, Comment.task_id == Task.id)
            .where(
                Task.project_id.in_(accessible_project_ids(user_id)),
                Task.deleted_at.is_(None),
                Comment.deleted_at.is_(None),
            )
        )

        if task_id is not None:
            statement = statement.where(Comment.task_id == task_id)

        statement = statement.order_by(Comment.created_at.asc())

        return list(self.db.scalars(statement).all())

    def get_for_user(
        self,
        comment_id: int,
        user_id: int,
    ) -> Comment | None:
        statement = (
            select(Comment)
            .join(Task, Comment.task_id == Task.id)
            .where(
                Comment.id == comment_id,
                Task.project_id.in_(accessible_project_ids(user_id)),
                Task.deleted_at.is_(None),
                Comment.deleted_at.is_(None),
            )
        )

        return self.db.scalar(statement)
