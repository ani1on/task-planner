from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ...api.deps import get_current_user
from ...database import get_db
from ...models.user import User
from ...schemas.activity import ActivityResponse
from ...services.activity import ActivityService

router = APIRouter(
    prefix="/activity",
    tags=["Activity"],
)


@router.get(
    "",
    response_model=list[ActivityResponse],
)
def list_activity(
    project_id: int | None = None,
    task_id: int | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ActivityResponse]:
    service = ActivityService(db)

    entries = service.list(
        user_id=current_user.id,
        project_id=project_id,
        task_id=task_id,
        limit=limit,
        offset=offset,
    )

    return [ActivityResponse.model_validate(entry) for entry in entries]
