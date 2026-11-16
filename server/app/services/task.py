from sqlalchemy.orm import Session

from ..core.errors import AppException
from ..core.time import utcnow
from ..models.tag import Tag
from ..models.task import Task
from ..models.task_tag import TaskTag
from ..realtime import events, project_room, publish
from ..repositories.project import ProjectRepository
from ..repositories.tag import TagRepository
from ..repositories.task import TaskRepository
from ..repositories.task_tag import TaskTagRepository
from ..schemas.task import SubtaskCreate, TaskCreate, TaskUpdate
from .access import AccessService
from .activity import ActivityService
from .notification import NotificationService
from .recurrence import RecurrenceService


class TaskService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.tasks = TaskRepository(db)
        self.projects = ProjectRepository(db)
        self.tags = TagRepository(db)
        self.task_tags = TaskTagRepository(db)
        self.access = AccessService(db)
        self.activity = ActivityService(db)
        self.notifications = NotificationService(db)
        self.recurrences = RecurrenceService(db)

    def list(
        self,
        user_id: int,
        project_id: int | None = None,
        status: str | None = None,
        priority: str | None = None,
        assignee_id: int | None = None,
        tag_id: int | None = None,
        search: str | None = None,
    ) -> list[Task]:
        return self.tasks.list_for_user(
            user_id=user_id,
            project_id=project_id,
            status=status,
            priority=priority,
            assignee_id=assignee_id,
            tag_id=tag_id,
            search=search,
        )

    def get(
        self,
        task_id: int,
        user_id: int,
    ) -> Task:
        task = self.tasks.get_for_user(task_id, user_id)

        if task is None:
            raise AppException(
                status_code=404,
                detail="Task not found",
                code="task_not_found",
            )

        return task

    def create(
        self,
        user_id: int,
        data: TaskCreate,
    ) -> Task:
        project = self.projects.get_for_user(data.project_id, user_id)

        if project is None:
            raise AppException(
                status_code=404,
                detail="Project not found",
                code="project_not_found",
            )

        self.access.require_role(data.project_id, user_id, "member")

        if data.assignee_id is not None:
            self._check_assignee(data.project_id, data.assignee_id)

        if data.parent_task_id is not None:
            parent = self.tasks.get_for_user(data.parent_task_id, user_id)

            if parent is None:
                raise AppException(
                    status_code=404,
                    detail="Parent task not found",
                    code="parent_task_not_found",
                )

        task = Task(
            project_id=data.project_id,
            created_by_id=user_id,
            parent_task_id=data.parent_task_id,
            assignee_id=data.assignee_id,
            title=data.title,
            description=data.description,
            status=data.status,
            priority=data.priority,
            start_at=data.start_at,
            due_at=data.due_at,
            position=data.position,
        )

        if task.status == "done":
            task.completed_at = utcnow()

        task = self.tasks.create(task)

        self.activity.log(
            user_id=user_id,
            action="task_created",
            entity_type="task",
            entity_id=task.id,
            project_id=task.project_id,
            task_id=task.id,
            new_values={
                "title": task.title,
                "status": task.status,
                "priority": task.priority,
            },
        )

        if task.assignee_id is not None:
            self._notify_assignee(user_id, task)

        publish(
            project_room(task.project_id),
            events.TASK_CREATED,
            {
                "id": task.id,
                "project_id": task.project_id,
                "status": task.status,
                "assignee_id": task.assignee_id,
            },
        )

        return task

    def update(
        self,
        task: Task,
        user_id: int,
        data: TaskUpdate,
    ) -> Task:
        self.access.require_role(task.project_id, user_id, "member")

        changes = data.model_dump(exclude_unset=True)

        if "assignee_id" in changes and changes["assignee_id"] is not None:
            self._check_assignee(task.project_id, changes["assignee_id"])

        old_values = {
            field: getattr(task, field)
            for field in changes
        }

        old_status = task.status
        old_assignee_id = task.assignee_id

        for field, value in changes.items():
            setattr(task, field, value)

        if "status" in changes:
            if task.status == "done":
                task.completed_at = utcnow()
            else:
                task.completed_at = None

        self.db.flush()

        self.activity.log(
            user_id=user_id,
            action="task_updated",
            entity_type="task",
            entity_id=task.id,
            project_id=task.project_id,
            task_id=task.id,
            old_values=old_values,
            new_values=changes,
        )

        if (
            "assignee_id" in changes
            and task.assignee_id != old_assignee_id
            and task.assignee_id is not None
        ):
            self._notify_assignee(user_id, task)

            publish(
                project_room(task.project_id),
                events.TASK_ASSIGNED,
                {
                    "id": task.id,
                    "project_id": task.project_id,
                    "assignee_id": task.assignee_id,
                },
            )

        if old_status != "done" and task.status == "done":
            next_task = self.recurrences.create_next_instance(task)

            if next_task is not None:
                self.activity.log(
                    user_id=user_id,
                    action="task_recurrence_created",
                    entity_type="task",
                    entity_id=next_task.id,
                    project_id=next_task.project_id,
                    task_id=next_task.id,
                    new_values={
                        "title": next_task.title,
                        "start_at": next_task.start_at,
                        "due_at": next_task.due_at,
                    },
                )

        publish(
            project_room(task.project_id),
            events.TASK_UPDATED,
            {
                "id": task.id,
                "project_id": task.project_id,
                "status": task.status,
                "priority": task.priority,
                "assignee_id": task.assignee_id,
            },
        )

        return task

    def soft_delete(
        self,
        task: Task,
        user_id: int,
    ) -> None:
        self.access.require_role(task.project_id, user_id, "member")

        task.deleted_at = utcnow()

        self.db.flush()

        self.activity.log(
            user_id=user_id,
            action="task_deleted",
            entity_type="task",
            entity_id=task.id,
            project_id=task.project_id,
            task_id=task.id,
            old_values={"title": task.title},
        )

        publish(
            project_room(task.project_id),
            events.TASK_DELETED,
            {
                "id": task.id,
                "project_id": task.project_id,
            },
        )

    # ------------------------------------------------------------------
    # Подзадачи
    # ------------------------------------------------------------------

    def list_subtasks(self, task: Task) -> list[Task]:
        return self.tasks.list_subtasks(task.id)

    def subtask_progress(self, task: Task) -> tuple[int, int]:
        subtasks = self.tasks.list_subtasks(task.id)

        total = len(subtasks)
        completed = sum(1 for subtask in subtasks if subtask.status == "done")

        return total, completed

    def create_subtask(
        self,
        parent: Task,
        user_id: int,
        data: SubtaskCreate,
    ) -> Task:
        self.access.require_role(parent.project_id, user_id, "member")

        if data.assignee_id is not None:
            self._check_assignee(parent.project_id, data.assignee_id)

        subtask = Task(
            project_id=parent.project_id,
            created_by_id=parent.created_by_id,
            parent_task_id=parent.id,
            assignee_id=data.assignee_id,
            title=data.title,
            description=data.description,
            status=data.status,
            priority=data.priority,
            start_at=data.start_at,
            due_at=data.due_at,
            position=data.position,
        )

        if subtask.status == "done":
            subtask.completed_at = utcnow()

        subtask = self.tasks.create(subtask)

        self.activity.log(
            user_id=user_id,
            action="subtask_created",
            entity_type="task",
            entity_id=subtask.id,
            project_id=subtask.project_id,
            task_id=subtask.id,
            new_values={
                "title": subtask.title,
                "parent_task_id": subtask.parent_task_id,
            },
        )

        publish(
            project_room(subtask.project_id),
            events.TASK_CREATED,
            {
                "id": subtask.id,
                "project_id": subtask.project_id,
                "parent_task_id": subtask.parent_task_id,
                "status": subtask.status,
            },
        )

        return subtask

    # ------------------------------------------------------------------
    # Теги задачи
    # ------------------------------------------------------------------

    def list_tags(self, task: Task) -> list[Tag]:
        return self.task_tags.list_tags_for_task(task.id)

    def add_tag(
        self,
        task: Task,
        tag_id: int,
        user_id: int,
    ) -> Tag:
        tag = self.tags.get_for_user(tag_id, user_id)

        if tag is None:
            raise AppException(
                status_code=404,
                detail="Tag not found",
                code="tag_not_found",
            )

        if tag.project_id != task.project_id:
            raise AppException(
                status_code=400,
                detail="Tag belongs to another project",
                code="tag_project_mismatch",
            )

        existing = self.task_tags.get(task.id, tag_id)

        if existing is not None:
            raise AppException(
                status_code=409,
                detail="Tag is already attached to the task",
                code="task_tag_already_exists",
            )

        self.task_tags.create(
            TaskTag(task_id=task.id, tag_id=tag_id),
        )

        return tag

    def remove_tag(
        self,
        task: Task,
        tag_id: int,
    ) -> None:
        link = self.task_tags.get(task.id, tag_id)

        if link is None:
            raise AppException(
                status_code=404,
                detail="Tag is not attached to the task",
                code="task_tag_not_found",
            )

        self.task_tags.delete(link)

    # ------------------------------------------------------------------
    # Вспомогательные методы
    # ------------------------------------------------------------------

    def _check_assignee(
        self,
        project_id: int,
        assignee_id: int,
    ) -> None:
        if self.access.role(project_id, assignee_id) is None:
            raise AppException(
                status_code=400,
                detail="Assignee is not a project member",
                code="assignee_not_project_member",
            )

    def _notify_assignee(
        self,
        actor_id: int,
        task: Task,
    ) -> None:
        if task.assignee_id is None:
            return

        self.notifications.notify(
            user_id=task.assignee_id,
            type="task_assigned",
            title="Вам назначена задача",
            message=f"Задача: {task.title}",
            task_id=task.id,
            project_id=task.project_id,
            actor_id=actor_id,
        )
