from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.checklist import Checklist
from ..models.task import Task
from .base import BaseRepository
from .project import accessible_project_ids


class ChecklistRepository(BaseRepository[Checklist]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Checklist)

    def list_for_user(
        self,
        user_id: int,
        task_id: int | None = None,
    ) -> list[Checklist]:
        statement = (
            select(Checklist)
            .join(Task, Checklist.task_id == Task.id)
            .where(
                Task.project_id.in_(accessible_project_ids(user_id)),
                Task.deleted_at.is_(None),
            )
        )

        if task_id is not None:
            statement = statement.where(Checklist.task_id == task_id)

        statement = statement.order_by(Checklist.position.asc())

        return list(self.db.scalars(statement).all())

    def get_for_user(
        self,
        checklist_id: int,
        user_id: int,
    ) -> Checklist | None:
        statement = (
            select(Checklist)
            .join(Task, Checklist.task_id == Task.id)
            .where(
                Checklist.id == checklist_id,
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
    ) -> list[Checklist]:
        statement = (
            select(Checklist)
            .join(Task, Checklist.task_id == Task.id)
            .where(
                Task.project_id.in_(accessible_project_ids(user_id)),
                Task.deleted_at.is_(None),
                Checklist.title.ilike(f"%{query}%"),
            )
            .order_by(Checklist.updated_at.desc())
            .limit(limit)
        )

        return list(self.db.scalars(statement).all())
