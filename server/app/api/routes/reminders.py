from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ...api.deps import get_current_user
from ...database import get_db
from ...models.user import User
from ...schemas.common import MessageResponse
from ...schemas.reminder import (
    ReminderCreate,
    ReminderProcessResponse,
    ReminderResponse,
    ReminderUpdate,
)
from ...services.reminder import ReminderService

router = APIRouter(
    prefix="/reminders",
    tags=["Reminders"],
)


@router.get(
    "",
    response_model=list[ReminderResponse],
)
def list_reminders(
    status_filter: str | None = None,
    task_id: int | None = None,
    event_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ReminderResponse]:
    service = ReminderService(db)

    reminders = service.list(
        current_user.id,
        status=status_filter,
        task_id=task_id,
        event_id=event_id,
    )

    return [ReminderResponse.model_validate(r) for r in reminders]


@router.post(
    "/process-due",
    response_model=ReminderProcessResponse,
)
def process_due_reminders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReminderProcessResponse:
    service = ReminderService(db)

    processed = service.process_due()

    db.commit()

    return ReminderProcessResponse(processed=processed)


@router.get(
    "/{reminder_id}",
    response_model=ReminderResponse,
)
def get_reminder(
    reminder_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReminderResponse:
    service = ReminderService(db)

    reminder = service.get(reminder_id, current_user.id)

    return ReminderResponse.model_validate(reminder)


@router.post(
    "",
    response_model=ReminderResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_reminder(
    data: ReminderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReminderResponse:
    service = ReminderService(db)

    reminder = service.create(current_user.id, data)

    db.commit()

    return ReminderResponse.model_validate(reminder)


@router.patch(
    "/{reminder_id}",
    response_model=ReminderResponse,
)
def update_reminder(
    reminder_id: int,
    data: ReminderUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReminderResponse:
    service = ReminderService(db)

    reminder = service.get(reminder_id, current_user.id)
    reminder = service.update(reminder, data)

    db.commit()

    return ReminderResponse.model_validate(reminder)


@router.delete(
    "/{reminder_id}",
    response_model=MessageResponse,
)
def delete_reminder(
    reminder_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    service = ReminderService(db)

    reminder = service.get(reminder_id, current_user.id)

    service.delete(reminder)

    db.commit()

    return MessageResponse(message="Reminder deleted")
