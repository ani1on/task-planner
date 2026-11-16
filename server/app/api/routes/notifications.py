from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ...api.deps import get_current_user
from ...database import get_db
from ...models.user import User
from ...schemas.common import MessageResponse
from ...schemas.notification import (
    NotificationCreate,
    NotificationResponse,
    UnreadCountResponse,
)
from ...services.notification import NotificationService

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
)


@router.get(
    "",
    response_model=list[NotificationResponse],
)
def list_notifications(
    is_read: bool | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[NotificationResponse]:
    service = NotificationService(db)

    notifications = service.list(current_user.id, is_read)

    return [NotificationResponse.model_validate(n) for n in notifications]


@router.get(
    "/unread-count",
    response_model=UnreadCountResponse,
)
def unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UnreadCountResponse:
    service = NotificationService(db)

    return UnreadCountResponse(count=service.unread_count(current_user.id))


@router.post(
    "",
    response_model=NotificationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_notification(
    data: NotificationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NotificationResponse:
    service = NotificationService(db)

    notification = service.create(current_user.id, data)

    db.commit()

    return NotificationResponse.model_validate(notification)


@router.post(
    "/read-all",
    response_model=MessageResponse,
)
def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    service = NotificationService(db)

    count = service.mark_all_read(current_user.id)

    db.commit()

    return MessageResponse(message=f"{count} notifications marked as read")


@router.post(
    "/{notification_id}/read",
    response_model=NotificationResponse,
)
def mark_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NotificationResponse:
    service = NotificationService(db)

    notification = service.get(notification_id, current_user.id)
    notification = service.mark_read(notification)

    db.commit()

    return NotificationResponse.model_validate(notification)


@router.delete(
    "/{notification_id}",
    response_model=MessageResponse,
)
def delete_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    service = NotificationService(db)

    notification = service.get(notification_id, current_user.id)

    service.delete(notification)

    db.commit()

    return MessageResponse(message="Notification deleted")
