from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models.notification import Notification
from .base import BaseRepository


class NotificationRepository(BaseRepository[Notification]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Notification)

    def list_for_user(
        self,
        user_id: int,
        is_read: bool | None = None,
    ) -> list[Notification]:
        statement = select(Notification).where(
            Notification.user_id == user_id,
        )

        if is_read is not None:
            statement = statement.where(Notification.is_read == is_read)

        statement = statement.order_by(Notification.created_at.desc())

        return list(self.db.scalars(statement).all())

    def get_for_user(
        self,
        notification_id: int,
        user_id: int,
    ) -> Notification | None:
        statement = select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )

        return self.db.scalar(statement)

    def count_unread(self, user_id: int) -> int:
        statement = select(func.count(Notification.id)).where(
            Notification.user_id == user_id,
            Notification.is_read.is_(False),
        )

        return self.db.scalar(statement) or 0

    def list_unread(self, user_id: int) -> list[Notification]:
        statement = select(Notification).where(
            Notification.user_id == user_id,
            Notification.is_read.is_(False),
        )

        return list(self.db.scalars(statement).all())
