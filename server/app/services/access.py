from sqlalchemy.orm import Session

from ..core.errors import AppException
from ..models.project import Project
from ..repositories.project import ProjectRepository
from ..repositories.project_member import ProjectMemberRepository

ROLE_LEVELS = {
    "viewer": 1,
    "member": 2,
    "admin": 3,
    "owner": 4,
}


class AccessService:
    """Проверка ролей пользователя в проекте."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.projects = ProjectRepository(db)
        self.members = ProjectMemberRepository(db)

    def role(
        self,
        project_id: int,
        user_id: int,
    ) -> str | None:
        project = self.projects.get_by_id(project_id)

        if project is None:
            return None

        if project.owner_id == user_id:
            return "owner"

        member = self.members.get(project_id, user_id)

        return member.role if member is not None else None

    def require_role(
        self,
        project_id: int,
        user_id: int,
        minimum: str = "viewer",
    ) -> str:
        role = self.role(project_id, user_id)

        if role is None:
            raise AppException(
                status_code=404,
                detail="Project not found",
                code="project_not_found",
            )

        if ROLE_LEVELS[role] < ROLE_LEVELS[minimum]:
            raise AppException(
                status_code=403,
                detail="Insufficient project permissions",
                code="permission_denied",
            )

        return role

    def require_project(
        self,
        project_id: int,
        user_id: int,
        minimum: str = "viewer",
    ) -> Project:
        self.require_role(project_id, user_id, minimum)

        project = self.projects.get_by_id(project_id)

        if project is None:
            raise AppException(
                status_code=404,
                detail="Project not found",
                code="project_not_found",
            )

        return project
