from datetime import datetime

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ...api.deps import get_current_user
from ...database import get_db
from ...models.user import User
from ...schemas.common import MessageResponse
from ...schemas.event import (
    EventCreate,
    EventResponse,
    EventUpdate,
)
from ...services.event import EventService

router = APIRouter(
    prefix="/events",
    tags=["Events"],
)


@router.get(
    "",
    response_model=list[EventResponse],
)
def list_events(
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    project_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[EventResponse]:
    service = EventService(db)

    events = service.list(
        user_id=current_user.id,
        date_from=date_from,
        date_to=date_to,
        project_id=project_id,
    )

    return [EventResponse.model_validate(event) for event in events]


@router.get(
    "/{event_id}",
    response_model=EventResponse,
)
def get_event(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EventResponse:
    service = EventService(db)

    event = service.get(event_id, current_user.id)

    return EventResponse.model_validate(event)


@router.post(
    "",
    response_model=EventResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_event(
    data: EventCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EventResponse:
    service = EventService(db)

    event = service.create(current_user.id, data)

    db.commit()

    return EventResponse.model_validate(event)


@router.patch(
    "/{event_id}",
    response_model=EventResponse,
)
def update_event(
    event_id: int,
    data: EventUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EventResponse:
    service = EventService(db)

    event = service.get(event_id, current_user.id)
    event = service.update(event, current_user.id, data)

    db.commit()

    return EventResponse.model_validate(event)


@router.delete(
    "/{event_id}",
    response_model=MessageResponse,
)
def delete_event(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    service = EventService(db)

    event = service.get(event_id, current_user.id)

    service.soft_delete(event)

    db.commit()

    return MessageResponse(message="Event deleted")
