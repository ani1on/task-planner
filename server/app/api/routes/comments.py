from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ...api.deps import get_current_user
from ...database import get_db
from ...models.user import User
from ...schemas.comment import (
    CommentCreate,
    CommentResponse,
    CommentUpdate,
)
from ...schemas.common import MessageResponse
from ...services.comment import CommentService

router = APIRouter(
    prefix="/comments",
    tags=["Comments"],
)


@router.get(
    "",
    response_model=list[CommentResponse],
)
def list_comments(
    task_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[CommentResponse]:
    service = CommentService(db)

    comments = service.list(current_user.id, task_id)

    return [CommentResponse.model_validate(c) for c in comments]


@router.get(
    "/{comment_id}",
    response_model=CommentResponse,
)
def get_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CommentResponse:
    service = CommentService(db)

    comment = service.get(comment_id, current_user.id)

    return CommentResponse.model_validate(comment)


@router.post(
    "",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_comment(
    data: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CommentResponse:
    service = CommentService(db)

    comment = service.create(current_user.id, data)

    db.commit()

    return CommentResponse.model_validate(comment)


@router.patch(
    "/{comment_id}",
    response_model=CommentResponse,
)
def update_comment(
    comment_id: int,
    data: CommentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CommentResponse:
    service = CommentService(db)

    comment = service.get(comment_id, current_user.id)
    comment = service.update(comment, current_user.id, data)

    db.commit()

    return CommentResponse.model_validate(comment)


@router.delete(
    "/{comment_id}",
    response_model=MessageResponse,
)
def delete_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    service = CommentService(db)

    comment = service.get(comment_id, current_user.id)

    service.soft_delete(comment, current_user.id)

    db.commit()

    return MessageResponse(message="Comment deleted")
