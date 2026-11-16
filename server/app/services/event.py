from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ..core.errors import AppException
from ..models.event import Event
from ..repositories.event import EventRepository
from ..repositories.project import ProjectRepository
from ..repositories.task import TaskRepository
from ..schemas.event import EventCreate, EventUpdate


class EventService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.events = EventRepository(db)
        self.projects = ProjectRepository(db)
        self.tasks = TaskRepository(db)

    def list(
        self,
        user_id: int,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        project_id: int | None = None,
    ) -> list[Event]:
        return self.events.list_for_user(
            user_id,
            date_from,
            date_to,
            project_id,
        )

    def get(
        self,
        event_id: int,
        user_id: int,
    ) -> Event:
        event = self.events.get_for_user(event_id, user_id)

        if event is None:
            raise AppException(
                status_code=404,
                detail="Event not found",
                code="event_not_found",
            )

        return event

    def create(
        self,
        user_id: int,
        data: EventCreate,
    ) -> Event:
        if data.end_at < data.start_at:
            raise AppException(
                status_code=400,
                detail="end_at must be after start_at",
                code="invalid_event_time",
            )

        self._check_links(user_id, data.project_id, data.task_id)

        event = Event(
            user_id=user_id,
            project_id=data.project_id,
            task_id=data.task_id,
            title=data.title,
            description=data.description,
            start_at=data.start_at,
            end_at=data.end_at,
            all_day=data.all_day,
            location=data.location,
        )

        return self.events.create(event)

    def update(
        self,
        event: Event,
        user_id: int,
        data: EventUpdate,
    ) -> Event:
        changes = data.model_dump(exclude_unset=True)

        self._check_links(
            user_id,
            changes.get("project_id"),
            changes.get("task_id"),
        )

        for field, value in changes.items():
            setattr(event, field, value)

        if event.end_at < event.start_at:
            raise AppException(
                status_code=400,
                detail="end_at must be after start_at",
                code="invalid_event_time",
            )

        self.db.flush()

        return event

    def soft_delete(self, event: Event) -> None:
        event.deleted_at = datetime.now(timezone.utc)

        self.db.flush()

    def _check_links(
        self,
        user_id: int,
        project_id: int | None,
        task_id: int | None,
    ) -> None:
        if project_id is not None:
            project = self.projects.get_for_user(project_id, user_id)

            if project is None:
                raise AppException(
                    status_code=404,
                    detail="Project not found",
                    code="project_not_found",
                )

        if task_id is not None:
            task = self.tasks.get_for_user(task_id, user_id)

            if task is None:
                raise AppException(
                    status_code=404,
                    detail="Task not found",
                    code="task_not_found",
                )
