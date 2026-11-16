from sqlalchemy.orm import Session

from ..core.errors import AppException
from ..models.project import Project
from ..realtime import events, project_room, publish
from ..repositories.project import ProjectRepository
from ..schemas.project import ProjectCreate, ProjectUpdate
from .access import AccessService
from .activity import ActivityService


class ProjectService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.projects = ProjectRepository(db)
        self.access = AccessService(db)
        self.activity = ActivityService(db)

    def list(
        self,
        user_id: int,
        status: str | None = None,
    ) -> list[Project]:
        return self.projects.list_for_user(user_id, status)

    def get(
        self,
        project_id: int,
        user_id: int,
    ) -> Project:
        project = self.projects.get_for_user(project_id, user_id)

        if project is None:
            raise AppException(
                status_code=404,
                detail="Project not found",
                code="project_not_found",
            )

        return project

    def progress(
        self,
        project_id: int,
    ) -> tuple[int, int]:
        return self.projects.progress_map([project_id]).get(project_id, (0, 0))

    def create(
        self,
        user_id: int,
        data: ProjectCreate,
    ) -> Project:
        project = Project(
            owner_id=user_id,
            name=data.name,
            description=data.description,
            color=data.color,
        )

        project = self.projects.create(project)

        self.activity.log(
            user_id=user_id,
            action="project_created",
            entity_type="project",
            entity_id=project.id,
            project_id=project.id,
            new_values={
                "name": project.name,
                "color": project.color,
            },
        )

        publish(
            project_room(project.id),
            events.PROJECT_UPDATED,
            {
                "id": project.id,
                "name": project.name,
                "status": project.status,
            },
        )

        return project

    def update(
        self,
        project: Project,
        user_id: int,
        data: ProjectUpdate,
    ) -> Project:
        self.access.require_role(project.id, user_id, "admin")

        changes = data.model_dump(exclude_unset=True)

        old_values = {
            field: getattr(project, field)
            for field in changes
        }

        for field, value in changes.items():
            setattr(project, field, value)

        self.db.flush()

        self.activity.log(
            user_id=user_id,
            action="project_updated",
            entity_type="project",
            entity_id=project.id,
            project_id=project.id,
            old_values=old_values,
            new_values=changes,
        )

        publish(
            project_room(project.id),
            events.PROJECT_UPDATED,
            {
                "id": project.id,
                "name": project.name,
                "status": project.status,
            },
        )

        return project

    def archive(
        self,
        project: Project,
        user_id: int,
    ) -> Project:
        self.access.require_role(project.id, user_id, "admin")

        old_status = project.status
        project.status = "archived"

        self.db.flush()

        self.activity.log(
            user_id=user_id,
            action="project_archived",
            entity_type="project",
            entity_id=project.id,
            project_id=project.id,
            old_values={"status": old_status},
            new_values={"status": project.status},
        )

        publish(
            project_room(project.id),
            events.PROJECT_UPDATED,
            {
                "id": project.id,
                "status": project.status,
            },
        )

        return project

    def hard_delete(
        self,
        project: Project,
        user_id: int,
    ) -> None:
        self.access.require_role(project.id, user_id, "owner")

        project_id = project.id

        self.activity.log(
            user_id=user_id,
            action="project_deleted",
            entity_type="project",
            entity_id=project_id,
            project_id=project_id,
            old_values={"name": project.name},
        )

        self.projects.delete(project)

        publish(
            project_room(project_id),
            events.PROJECT_DELETED,
            {"id": project_id},
        )
