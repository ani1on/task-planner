from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ...api.deps import get_current_user
from ...database import get_db
from ...models.user import User
from ...schemas.common import MessageResponse
from ...schemas.tag import (
    TagCreate,
    TagResponse,
    TagUpdate,
)
from ...services.tag import TagService

router = APIRouter(
    prefix="/tags",
    tags=["Tags"],
)


@router.get(
    "",
    response_model=list[TagResponse],
)
def list_tags(
    project_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[TagResponse]:
    service = TagService(db)

    tags = service.list(current_user.id, project_id)

    return [TagResponse.model_validate(tag) for tag in tags]


@router.get(
    "/{tag_id}",
    response_model=TagResponse,
)
def get_tag(
    tag_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TagResponse:
    service = TagService(db)

    tag = service.get(tag_id, current_user.id)

    return TagResponse.model_validate(tag)


@router.post(
    "",
    response_model=TagResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_tag(
    data: TagCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TagResponse:
    service = TagService(db)

    tag = service.create(current_user.id, data)

    db.commit()

    return TagResponse.model_validate(tag)


@router.patch(
    "/{tag_id}",
    response_model=TagResponse,
)
def update_tag(
    tag_id: int,
    data: TagUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TagResponse:
    service = TagService(db)

    tag = service.get(tag_id, current_user.id)
    tag = service.update(tag, current_user.id, data)

    db.commit()

    return TagResponse.model_validate(tag)


@router.delete(
    "/{tag_id}",
    response_model=MessageResponse,
)
def delete_tag(
    tag_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    service = TagService(db)

    tag = service.get(tag_id, current_user.id)

    service.delete(tag, current_user.id)

    db.commit()

    return MessageResponse(message="Tag deleted")
