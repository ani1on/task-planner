from datetime import datetime

from sqlalchemy.orm import Session

from ..core.errors import AppException
from ..core.time import ensure_utc, utcnow
from ..models.reminder import Reminder
from ..realtime import events, publish, user_room
from ..repositories.event import EventRepository
from ..repositories.reminder import ReminderRepository
from ..repositories.task import TaskRepository
from ..schemas.reminder import ReminderCreate, ReminderUpdate
from .activity import ActivityService
from .notification import NotificationService


class ReminderService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.reminders = ReminderRepository(db)
        self.tasks = TaskRepository(db)
        self.events = EventRepository(db)
        self.activity = ActivityService(db)
        self.notifications = NotificationService(db)

    def list(
        self,
        user_id: int,
        status: str | None = None,
        task_id: int | None = None,
        event_id: int | None = None,
    ) -> list[Reminder]:
        return self.reminders.list_for_user(
            user_id=user_id,
            status=status,
            task_id=task_id,
            event_id=event_id,
        )

    def get(
        self,
        reminder_id: int,
        user_id: int,
    ) -> Reminder:
        reminder = self.reminders.get_for_user(reminder_id, user_id)

        if reminder is None:
            raise AppException(
                status_code=404,
                detail="Reminder not found",
                code="reminder_not_found",
            )

        return reminder

    def create(
        self,
        user_id: int,
        data: ReminderCreate,
    ) -> Reminder:
        if data.task_id is None and data.event_id is None:
            raise AppException(
                status_code=400,
                detail="Reminder must be linked to a task or an event",
                code="reminder_target_required",
            )

        project_id = None

        if data.task_id is not None:
            task = self.tasks.get_for_user(data.task_id, user_id)

            if task is None:
                raise AppException(
                    status_code=404,
                    detail="Task not found",
                    code="task_not_found",
                )

            project_id = task.project_id

        if data.event_id is not None:
            event = self.events.get_for_user(data.event_id, user_id)

            if event is None:
                raise AppException(
                    status_code=404,
                    detail="Event not found",
                    code="event_not_found",
                )

        reminder = Reminder(
            user_id=user_id,
            task_id=data.task_id,
            event_id=data.event_id,
            remind_at=data.remind_at,
            channel=data.channel,
            status="pending",
        )

        reminder = self.reminders.create(reminder)

        self.activity.log(
            user_id=user_id,
            action="reminder_created",
            entity_type="reminder",
            entity_id=reminder.id,
            project_id=project_id,
            task_id=data.task_id,
            new_values={
                "remind_at": reminder.remind_at,
                "channel": reminder.channel,
            },
        )

        return reminder

    def update(
        self,
        reminder: Reminder,
        data: ReminderUpdate,
    ) -> Reminder:
        changes = data.model_dump(exclude_unset=True)

        for field, value in changes.items():
            setattr(reminder, field, value)

        self.db.flush()

        return reminder

    def delete(self, reminder: Reminder) -> None:
        self.reminders.delete(reminder)

    def process_due(
        self,
        now: datetime | None = None,
    ) -> int:
        """Создаёт уведомления для всех наступивших напоминаний."""
        current = ensure_utc(now or utcnow())

        due = [
            reminder
            for reminder in self.reminders.list_pending()
            if ensure_utc(reminder.remind_at) <= current
        ]

        for reminder in due:
            self.notifications.notify(
                user_id=reminder.user_id,
                type="reminder",
                title="Напоминание",
                message=self._message(reminder),
                task_id=reminder.task_id,
            )

            reminder.status = "sent"
            reminder.sent_at = current

            publish(
                user_room(reminder.user_id),
                events.REMINDER_SENT,
                {
                    "id": reminder.id,
                    "task_id": reminder.task_id,
                    "event_id": reminder.event_id,
                    "remind_at": reminder.remind_at,
                },
            )

        self.db.flush()

        return len(due)

    def _message(self, reminder: Reminder) -> str:
        if reminder.task_id is not None:
            task = self.tasks.get_by_id(reminder.task_id)

            if task is not None:
                return f"Задача: {task.title}"

        if reminder.event_id is not None:
            event = self.events.get_by_id(reminder.event_id)

            if event is not None:
                return f"Событие: {event.title}"

        return "Напоминание"
