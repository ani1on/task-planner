from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.reminder import Reminder
from .base import BaseRepository


class ReminderRepository(BaseRepository[Reminder]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Reminder)

    def list_for_user(
        self,
        user_id: int,
        status: str | None = None,
        task_id: int | None = None,
        event_id: int | None = None,
    ) -> list[Reminder]:
        statement = select(Reminder).where(Reminder.user_id == user_id)

        if status is not None:
            statement = statement.where(Reminder.status == status)

        if task_id is not None:
            statement = statement.where(Reminder.task_id == task_id)

        if event_id is not None:
            statement = statement.where(Reminder.event_id == event_id)

        statement = statement.order_by(Reminder.remind_at.asc())

        return list(self.db.scalars(statement).all())

    def get_for_user(
        self,
        reminder_id: int,
        user_id: int,
    ) -> Reminder | None:
        statement = select(Reminder).where(
            Reminder.id == reminder_id,
            Reminder.user_id == user_id,
        )

        return self.db.scalar(statement)

    def list_pending(
        self,
        before: datetime | None = None,
    ) -> list[Reminder]:
        statement = select(Reminder).where(
            Reminder.status == "pending",
        )

        if before is not None:
            statement = statement.where(Reminder.remind_at <= before)

        statement = statement.order_by(Reminder.remind_at.asc())

        return list(self.db.scalars(statement).all())
