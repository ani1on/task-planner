from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.checklist import Checklist
from ..models.checklist_item import ChecklistItem
from ..models.project import Project
from ..models.task import Task
from .base import BaseRepository


class ChecklistItemRepository(BaseRepository[ChecklistItem]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, ChecklistItem)

    def list_for_checklist(
        self,
        checklist_id: int,
    ) -> list[ChecklistItem]:
        statement = (
            select(ChecklistItem)
            .where(ChecklistItem.checklist_id == checklist_id)
            .order_by(ChecklistItem.position.asc())
        )

        return list(self.db.scalars(statement).all())

    def get_for_user(
        self,
        item_id: int,
        user_id: int,
    ) -> ChecklistItem | None:
        statement = (
            select(ChecklistItem)
            .join(Checklist, ChecklistItem.checklist_id == Checklist.id)
            .join(Task, Checklist.task_id == Task.id)
            .join(Project, Task.project_id == Project.id)
            .where(
                ChecklistItem.id == item_id,
                Project.owner_id == user_id,
                Task.deleted_at.is_(None),
            )
        )

        return self.db.scalar(statement)
