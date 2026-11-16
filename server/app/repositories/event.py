from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.event import Event
from .base import BaseRepository


class EventRepository(BaseRepository[Event]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Event)

    def list_for_user(
        self,
        user_id: int,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        project_id: int | None = None,
    ) -> list[Event]:
        statement = select(Event).where(
            Event.user_id == user_id,
            Event.deleted_at.is_(None),
        )

        if date_from is not None:
            statement = statement.where(Event.end_at >= date_from)

        if date_to is not None:
            statement = statement.where(Event.start_at <= date_to)

        if project_id is not None:
            statement = statement.where(Event.project_id == project_id)

        statement = statement.order_by(Event.start_at.asc())

        return list(self.db.scalars(statement).all())

    def get_for_user(
        self,
        event_id: int,
        user_id: int,
    ) -> Event | None:
        statement = select(Event).where(
            Event.id == event_id,
            Event.user_id == user_id,
            Event.deleted_at.is_(None),
        )

        return self.db.scalar(statement)
