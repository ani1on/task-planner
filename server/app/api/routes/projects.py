from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ...api.deps import get_current_user
from ...api.serializers import project_response
from ...database import get_db
from ...models.user import User
from ...repositories.project import ProjectRepository
from ...schemas.common import MessageResponse
from ...schemas.dashboard import ProjectProgressResponse
from ...schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from ...services.access import AccessService
from ...services.project import ProjectService

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get(
    "",
    response_model=list[ProjectResponse],
)
def list_projects(
    status_filter: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ProjectResponse]:
    service = ProjectService(db)

    projects = service.list(user_id=current_user.id, status=status_filter)

    progress = ProjectRepository(db).progress_map(
        [project.id for project in projects],
    )
    access = AccessService(db)

    return [
        project_response(
            project,
            role=access.role(project.id, current_user.id),
            progress=progress.get(project.id, (0, 0)),
        )
        for project in projects
    ]


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
)
def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectResponse:
    service = ProjectService(db)

    project = service.get(project_id, current_user.id)

    return project_response(
        project,
        role=AccessService(db).role(project.id, current_user.id),
        progress=service.progress(project.id),
    )


@router.get(
    "/{project_id}/progress",
    response_model=ProjectProgressResponse,
)
def get_project_progress(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectProgressResponse:
    service = ProjectService(db)

    project = service.get(project_id, current_user.id)
    total, done = service.progress(project.id)

    return ProjectProgressResponse(
        project_id=project.id,
        tasks_total=total,
        tasks_done=done,
        progress=int(done / total * 100) if total else 0,
    )


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_project(
    data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectResponse:
    service = ProjectService(db)

    project = service.create(current_user.id, data)

    db.commit()

    return project_response(
        project,
        role="owner",
        progress=(0, 0),
    )


@router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
)
def update_project(
    project_id: int,
    data: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectResponse:
    service = ProjectService(db)

    project = service.get(project_id, current_user.id)
    project = service.update(project, current_user.id, data)

    db.commit()

    return project_response(
        project,
        role=AccessService(db).role(project.id, current_user.id),
        progress=service.progress(project.id),
    )


@router.post(
    "/{project_id}/archive",
    response_model=ProjectResponse,
)
def archive_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectResponse:
    service = ProjectService(db)

    project = service.get(project_id, current_user.id)
    project = service.archive(project, current_user.id)

    db.commit()

    return project_response(
        project,
        role=AccessService(db).role(project.id, current_user.id),
        progress=service.progress(project.id),
    )


@router.delete(
    "/{project_id}",
    response_model=MessageResponse,
)
def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    service = ProjectService(db)

    project = service.get(project_id, current_user.id)

    service.hard_delete(project, current_user.id)

    db.commit()

    return MessageResponse(message="Project deleted")
