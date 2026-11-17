import calendar
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from ..core.errors import AppException
from ..core.time import ensure_utc
from ..models.task import Task
from ..models.task_recurrence import TaskRecurrence
from ..repositories.task import TaskRepository
from ..repositories.task_recurrence import TaskRecurrenceRepository
from ..schemas.recurrence import RecurrenceCreate, RecurrenceUpdate


class RecurrenceService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.recurrences = TaskRecurrenceRepository(db)
        self.tasks = TaskRepository(db)

    def get(self, task: Task) -> TaskRecurrence | None:
        return self.recurrences.get_for_task(task.id)

    def set(
        self,
        task: Task,
        data: RecurrenceCreate,
    ) -> TaskRecurrence:
        recurrence = self.recurrences.get_for_task(task.id)

        if recurrence is None:
            recurrence = TaskRecurrence(
                task_id=task.id,
                frequency=data.frequency,
                interval=data.interval,
                days_of_week=data.days_of_week,
                day_of_month=data.day_of_month,
                start_at=data.start_at,
                end_at=data.end_at,
                is_active=data.is_active,
            )

            recurrence.next_run_at = self.next_run(
                recurrence,
                ensure_utc(data.start_at),
            )

            return self.recurrences.create(recurrence)

        changes = data.model_dump()

        for field, value in changes.items():
            setattr(recurrence, field, value)

        recurrence.next_run_at = self.next_run(
            recurrence,
            ensure_utc(data.start_at),
        )

        self.db.flush()

        return recurrence

    def update(
        self,
        task: Task,
        data: RecurrenceUpdate,
    ) -> TaskRecurrence:
        recurrence = self.get(task)

        if recurrence is None:
            raise AppException(
                status_code=404,
                detail="Task recurrence not found",
                code="recurrence_not_found",
            )

        changes = data.model_dump(exclude_unset=True)

        for field, value in changes.items():
            setattr(recurrence, field, value)

        base = ensure_utc(changes.get("start_at") or recurrence.start_at)

        recurrence.next_run_at = self.next_run(recurrence, base)

        self.db.flush()

        return recurrence

    def delete(self, task: Task) -> None:
        recurrence = self.get(task)

        if recurrence is None:
            raise AppException(
                status_code=404,
                detail="Task recurrence not found",
                code="recurrence_not_found",
            )

        self.recurrences.delete(recurrence)

    def next_run(
        self,
        recurrence: TaskRecurrence,
        after: datetime,
    ) -> datetime:
        interval = max(recurrence.interval or 1, 1)
        after = ensure_utc(after)

        if recurrence.frequency == "daily":
            return after + timedelta(days=interval)

        if recurrence.frequency == "weekly":
            days = recurrence.days_of_week or []

            if days:
                anchor = ensure_utc(recurrence.start_at)
                anchor_week = (
                    anchor.date() - timedelta(days=anchor.isoweekday() - 1)
                )

                for day_offset in range(1, 7 * interval + 8):
                    candidate = after + timedelta(days=day_offset)
                    candidate_week = (
                        candidate.date()
                        - timedelta(days=candidate.isoweekday() - 1)
                    )
                    week_offset = (candidate_week - anchor_week).days // 7

                    if (
                        week_offset >= 0
                        and week_offset % interval == 0
                        and candidate.isoweekday() in days
                    ):
                        return candidate

            return after + timedelta(weeks=interval)

        if recurrence.frequency == "monthly":
            month_index = after.month - 1 + interval
            year = after.year + month_index // 12
            month = month_index % 12 + 1
            day = recurrence.day_of_month or recurrence.start_at.day
            day = min(day, calendar.monthrange(year, month)[1])
            return after.replace(year=year, month=month, day=day)

        return after + timedelta(days=interval)

    def create_next_instance(
        self,
        task: Task,
    ) -> Task | None:
        recurrence = self.get(task)

        if recurrence is None or not recurrence.is_active:
            return None

        if recurrence.next_run_at is None:
            return None

        next_start = ensure_utc(recurrence.next_run_at)

        if (
            recurrence.end_at is not None
            and next_start > ensure_utc(recurrence.end_at)
        ):
            recurrence.is_active = False
            self.db.flush()

            return None

        offset = None
        if task.start_at is not None and task.due_at is not None:
            offset = ensure_utc(task.due_at) - ensure_utc(task.start_at)
        elif task.due_at is not None:
            offset = ensure_utc(task.due_at) - ensure_utc(recurrence.start_at)

        next_task = Task(
            project_id=task.project_id,
            created_by_id=task.created_by_id,
            assignee_id=task.assignee_id,
            title=task.title,
            description=task.description,
            status="todo",
            priority=task.priority,
            position=task.position,
            start_at=recurrence.start_at,
            due_at=next_start + offset if offset is not None else None,
        )

        next_task = self.tasks.create(next_task)

        next_run_at = self.next_run(recurrence, next_start)

        self.recurrences.create(
            TaskRecurrence(
                task_id=next_task.id,
                frequency=recurrence.frequency,
                interval=recurrence.interval,
                days_of_week=recurrence.days_of_week,
                day_of_month=recurrence.day_of_month,
                start_at=next_start,
                end_at=recurrence.end_at,
                next_run_at=next_run_at,
                is_active=recurrence.is_active,
            ),
        )

        self.recurrences.delete(recurrence)

        return next_task
