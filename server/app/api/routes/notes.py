from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ...api.deps import get_current_user
from ...database import get_db
from ...models.user import User
from ...schemas.common import MessageResponse
from ...schemas.note import (
    NoteCreate,
    NoteResponse,
    NoteUpdate,
)
from ...services.note import NoteService

router = APIRouter(
    prefix="/notes",
    tags=["Notes"],
)


@router.get(
    "",
    response_model=list[NoteResponse],
)
def list_notes(
    project_id: int | None = None,
    task_id: int | None = None,
    search: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[NoteResponse]:
    service = NoteService(db)

    notes = service.list(
        user_id=current_user.id,
        project_id=project_id,
        task_id=task_id,
        search=search,
    )

    return [NoteResponse.model_validate(note) for note in notes]


@router.get(
    "/{note_id}",
    response_model=NoteResponse,
)
def get_note(
    note_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NoteResponse:
    service = NoteService(db)

    note = service.get(note_id, current_user.id)

    return NoteResponse.model_validate(note)


@router.post(
    "",
    response_model=NoteResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_note(
    data: NoteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NoteResponse:
    service = NoteService(db)

    note = service.create(current_user.id, data)

    db.commit()

    return NoteResponse.model_validate(note)


@router.patch(
    "/{note_id}",
    response_model=NoteResponse,
)
def update_note(
    note_id: int,
    data: NoteUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NoteResponse:
    service = NoteService(db)

    note = service.get(note_id, current_user.id)
    note = service.update(note, current_user.id, data)

    db.commit()

    return NoteResponse.model_validate(note)


@router.delete(
    "/{note_id}",
    response_model=MessageResponse,
)
def delete_note(
    note_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    service = NoteService(db)

    note = service.get(note_id, current_user.id)

    service.soft_delete(note)

    db.commit()

    return MessageResponse(message="Note deleted")
