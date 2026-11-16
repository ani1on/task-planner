from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...api.deps import get_current_user
from ...api.serializers import task_response
from ...database import get_db
from ...models.user import User
from ...schemas.dashboard import (
    DashboardProject,
    DashboardResponse,
    DashboardStats,
)
from ...services.dashboard import DashboardService

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


@router.get(
    "",
    response_model=DashboardResponse,
)
def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DashboardResponse:
    service = DashboardService(db)

    data = service.build(current_user.id)

    return DashboardResponse(
        stats=DashboardStats(**data["stats"]),
        projects=[
            DashboardProject(**project)
            for project in data["projects"]
        ],
        recent_projects=[
            DashboardProject(**project)
            for project in data["recent_projects"]
        ],
        upcoming_tasks=[
            task_response(task)
            for task in data["upcoming_tasks"]
        ],
        recent_tasks=[
            task_response(task)
            for task in data["recent_tasks"]
        ],
        total_projects=data["total_projects"],
    )
