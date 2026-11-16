from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ..core.errors import AppException
from ..models.notification import Notification
from ..realtime import publish, user_room
from ..realtime.events import NOTIFICATION_CREATED
from ..repositories.notification import NotificationRepository
from ..repositories.user_setting import UserSettingRepository
from ..schemas.notification import NotificationCreate


class NotificationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.notifications = NotificationRepository(db)
        self.settings = UserSettingRepository(db)

    def list(
        self,
        user_id: int,
        is_read: bool | None = None,
    ) -> list[Notification]:
        return self.notifications.list_for_user(user_id, is_read)

    def get(
        self,
        notification_id: int,
        user_id: int,
    ) -> Notification:
        notification = self.notifications.get_for_user(
            notification_id,
            user_id,
        )

        if notification is None:
            raise AppException(
                status_code=404,
                detail="Notification not found",
                code="notification_not_found",
            )

        return notification

    def unread_count(self, user_id: int) -> int:
        return self.notifications.count_unread(user_id)

    def create(
        self,
        user_id: int,
        data: NotificationCreate,
    ) -> Notification:
        notification = Notification(
            user_id=user_id,
            type=data.type,
            title=data.title,
            message=data.message,
            task_id=data.task_id,
            project_id=data.project_id,
        )

        return self.notifications.create(notification)

    def notify(
        self,
        *,
        user_id: int,
        type: str,
        title: str,
        message: str,
        task_id: int | None = None,
        project_id: int | None = None,
        actor_id: int | None = None,
    ) -> Notification | None:
        """Создаёт уведомление с учётом настроек пользователя."""
        if actor_id is not None and actor_id == user_id:
            return None

        setting = self.settings.get_by_user(user_id)

        if setting is not None and not setting.notification_enabled:
            return None

        notification = Notification(
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            task_id=task_id,
            project_id=project_id,
        )

        notification = self.notifications.create(notification)

        publish(
            user_room(user_id),
            NOTIFICATION_CREATED,
            {
                "id": notification.id,
                "type": notification.type,
                "title": notification.title,
                "message": notification.message,
                "task_id": notification.task_id,
                "project_id": notification.project_id,
            },
        )

        return notification

    def mark_read(self, notification: Notification) -> Notification:
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.now(timezone.utc)

            self.db.flush()

        return notification

    def mark_all_read(self, user_id: int) -> int:
        now = datetime.now(timezone.utc)

        unread = self.notifications.list_unread(user_id)

        for notification in unread:
            notification.is_read = True
            notification.read_at = now

        self.db.flush()

        return len(unread)

    def delete(self, notification: Notification) -> None:
        self.notifications.delete(notification)
