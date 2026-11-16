from sqlalchemy.orm import Session

from ..core.errors import AppException
from ..models.checklist import Checklist
from ..models.checklist_item import ChecklistItem
from ..repositories.checklist import ChecklistRepository
from ..repositories.checklist_item import ChecklistItemRepository
from ..repositories.task import TaskRepository
from ..schemas.checklist import (
    ChecklistCreate,
    ChecklistItemCreate,
    ChecklistItemUpdate,
    ChecklistUpdate,
)
from .access import AccessService
from .activity import ActivityService


class ChecklistService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.checklists = ChecklistRepository(db)
        self.items = ChecklistItemRepository(db)
        self.tasks = TaskRepository(db)
        self.access = AccessService(db)
        self.activity = ActivityService(db)

    def list(
        self,
        user_id: int,
        task_id: int | None = None,
    ) -> list[Checklist]:
        return self.checklists.list_for_user(user_id, task_id)

    def get(
        self,
        checklist_id: int,
        user_id: int,
    ) -> Checklist:
        checklist = self.checklists.get_for_user(checklist_id, user_id)

        if checklist is None:
            raise AppException(
                status_code=404,
                detail="Checklist not found",
                code="checklist_not_found",
            )

        return checklist

    def create(
        self,
        user_id: int,
        data: ChecklistCreate,
    ) -> Checklist:
        task = self.tasks.get_for_user(data.task_id, user_id)

        if task is None:
            raise AppException(
                status_code=404,
                detail="Task not found",
                code="task_not_found",
            )

        self.access.require_role(task.project_id, user_id, "member")

        checklist = Checklist(
            task_id=data.task_id,
            title=data.title,
            position=data.position,
        )

        checklist = self.checklists.create(checklist)

        self.activity.log(
            user_id=user_id,
            action="checklist_created",
            entity_type="checklist",
            entity_id=checklist.id,
            project_id=task.project_id,
            task_id=task.id,
            new_values={"title": checklist.title},
        )

        return checklist

    def update(
        self,
        checklist: Checklist,
        user_id: int,
        data: ChecklistUpdate,
    ) -> Checklist:
        self.access.require_role(
            checklist.task.project_id,
            user_id,
            "member",
        )

        changes = data.model_dump(exclude_unset=True)

        for field, value in changes.items():
            setattr(checklist, field, value)

        self.db.flush()

        return checklist

    def delete(
        self,
        checklist: Checklist,
        user_id: int,
    ) -> None:
        self.access.require_role(
            checklist.task.project_id,
            user_id,
            "member",
        )

        self.activity.log(
            user_id=user_id,
            action="checklist_deleted",
            entity_type="checklist",
            entity_id=checklist.id,
            project_id=checklist.task.project_id,
            task_id=checklist.task_id,
            old_values={"title": checklist.title},
        )

        self.checklists.delete(checklist)

    def list_items(
        self,
        checklist: Checklist,
    ) -> list[ChecklistItem]:
        return self.items.list_for_checklist(checklist.id)

    def get_item(
        self,
        item_id: int,
        user_id: int,
    ) -> ChecklistItem:
        item = self.items.get_for_user(item_id, user_id)

        if item is None:
            raise AppException(
                status_code=404,
                detail="Checklist item not found",
                code="checklist_item_not_found",
            )

        return item

    def create_item(
        self,
        checklist: Checklist,
        user_id: int,
        data: ChecklistItemCreate,
    ) -> ChecklistItem:
        self.access.require_role(
            checklist.task.project_id,
            user_id,
            "member",
        )

        item = ChecklistItem(
            checklist_id=checklist.id,
            content=data.content,
            position=data.position,
        )

        return self.items.create(item)

    def update_item(
        self,
        item: ChecklistItem,
        user_id: int,
        data: ChecklistItemUpdate,
    ) -> ChecklistItem:
        self.access.require_role(
            item.checklist.task.project_id,
            user_id,
            "member",
        )

        changes = data.model_dump(exclude_unset=True)

        for field, value in changes.items():
            setattr(item, field, value)

        self.db.flush()

        return item

    def delete_item(
        self,
        item: ChecklistItem,
        user_id: int,
    ) -> None:
        self.access.require_role(
            item.checklist.task.project_id,
            user_id,
            "member",
        )

        self.items.delete(item)
