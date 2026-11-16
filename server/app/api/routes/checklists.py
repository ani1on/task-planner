from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ...api.deps import get_current_user
from ...database import get_db
from ...models.user import User
from ...schemas.checklist import (
    ChecklistCreate,
    ChecklistItemCreate,
    ChecklistItemResponse,
    ChecklistItemUpdate,
    ChecklistResponse,
    ChecklistUpdate,
)
from ...schemas.common import MessageResponse
from ...services.checklist import ChecklistService

router = APIRouter(
    prefix="/checklists",
    tags=["Checklists"],
)

items_router = APIRouter(
    prefix="/checklist-items",
    tags=["Checklists"],
)


@router.get(
    "",
    response_model=list[ChecklistResponse],
)
def list_checklists(
    task_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ChecklistResponse]:
    service = ChecklistService(db)

    checklists = service.list(current_user.id, task_id)

    return [ChecklistResponse.model_validate(c) for c in checklists]


@router.get(
    "/{checklist_id}",
    response_model=ChecklistResponse,
)
def get_checklist(
    checklist_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChecklistResponse:
    service = ChecklistService(db)

    checklist = service.get(checklist_id, current_user.id)

    return ChecklistResponse.model_validate(checklist)


@router.post(
    "",
    response_model=ChecklistResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_checklist(
    data: ChecklistCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChecklistResponse:
    service = ChecklistService(db)

    checklist = service.create(current_user.id, data)

    db.commit()

    return ChecklistResponse.model_validate(checklist)


@router.patch(
    "/{checklist_id}",
    response_model=ChecklistResponse,
)
def update_checklist(
    checklist_id: int,
    data: ChecklistUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChecklistResponse:
    service = ChecklistService(db)

    checklist = service.get(checklist_id, current_user.id)
    checklist = service.update(checklist, current_user.id, data)

    db.commit()

    return ChecklistResponse.model_validate(checklist)


@router.delete(
    "/{checklist_id}",
    response_model=MessageResponse,
)
def delete_checklist(
    checklist_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    service = ChecklistService(db)

    checklist = service.get(checklist_id, current_user.id)

    service.delete(checklist, current_user.id)

    db.commit()

    return MessageResponse(message="Checklist deleted")


@router.get(
    "/{checklist_id}/items",
    response_model=list[ChecklistItemResponse],
)
def list_checklist_items(
    checklist_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ChecklistItemResponse]:
    service = ChecklistService(db)

    checklist = service.get(checklist_id, current_user.id)

    items = service.list_items(checklist)

    return [ChecklistItemResponse.model_validate(item) for item in items]


@router.post(
    "/{checklist_id}/items",
    response_model=ChecklistItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_checklist_item(
    checklist_id: int,
    data: ChecklistItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChecklistItemResponse:
    service = ChecklistService(db)

    checklist = service.get(checklist_id, current_user.id)

    item = service.create_item(checklist, current_user.id, data)

    db.commit()

    return ChecklistItemResponse.model_validate(item)


@items_router.patch(
    "/{item_id}",
    response_model=ChecklistItemResponse,
)
def update_checklist_item(
    item_id: int,
    data: ChecklistItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChecklistItemResponse:
    service = ChecklistService(db)

    item = service.get_item(item_id, current_user.id)
    item = service.update_item(item, current_user.id, data)

    db.commit()

    return ChecklistItemResponse.model_validate(item)


@items_router.delete(
    "/{item_id}",
    response_model=MessageResponse,
)
def delete_checklist_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    service = ChecklistService(db)

    item = service.get_item(item_id, current_user.id)

    service.delete_item(item, current_user.id)

    db.commit()

    return MessageResponse(message="Checklist item deleted")
