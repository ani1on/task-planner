from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ...api.deps import get_current_user
from ...database import get_db
from ...models.user import User
from ...schemas.common import MessageResponse
from ...schemas.member import (
    MemberInvite,
    MemberResponse,
    MemberUpdate,
    MemberUser,
)
from ...services.member import MemberService

router = APIRouter(
    prefix="/projects/{project_id}/members",
    tags=["Project members"],
)


@router.get(
    "",
    response_model=list[MemberResponse],
)
def list_members(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[MemberResponse]:
    service = MemberService(db)

    project, members = service.list(project_id, current_user.id)

    owner = MemberResponse(
        id=0,
        project_id=project.id,
        user_id=project.owner_id,
        role="owner",
        joined_at=project.created_at,
        user=MemberUser.model_validate(project.owner),
    )

    result = [owner]
    result.extend(
        MemberResponse.model_validate(member)
        for member in members
        if member.user_id != project.owner_id
    )

    return result


@router.post(
    "",
    response_model=MemberResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_member(
    project_id: int,
    data: MemberInvite,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MemberResponse:
    service = MemberService(db)

    member = service.add(project_id, current_user.id, data)

    db.commit()

    return MemberResponse.model_validate(member)


@router.patch(
    "/{user_id}",
    response_model=MemberResponse,
)
def update_member_role(
    project_id: int,
    user_id: int,
    data: MemberUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MemberResponse:
    service = MemberService(db)

    member = service.update_role(
        project_id,
        current_user.id,
        user_id,
        data,
    )

    db.commit()

    return MemberResponse.model_validate(member)


@router.delete(
    "/{user_id}",
    response_model=MessageResponse,
)
def remove_member(
    project_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    service = MemberService(db)

    service.remove(project_id, current_user.id, user_id)

    db.commit()

    return MessageResponse(message="Project member removed")
