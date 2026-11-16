from sqlalchemy import Select, case, func, or_, select
from sqlalchemy.orm import Session

from ..models.project import Project
from ..models.project_member import ProjectMember
from ..models.task import Task
from .base import BaseRepository


def accessible_project_ids(user_id: int) -> Select:
    """Подзапрос с id проектов, доступных пользователю.

    Владелец имеет доступ всегда, остальные — через project_members.
    """
    membership = select(ProjectMember.project_id).where(
        ProjectMember.user_id == user_id,
    )

    return select(Project.id).where(
        or_(
            Project.owner_id == user_id,
            Project.id.in_(membership),
        ),
    )


class ProjectRepository(BaseRepository[Project]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Project)

    def list_for_user(
        self,
        user_id: int,
        status: str | None = None,
    ) -> list[Project]:
        statement = select(Project).where(
            Project.id.in_(accessible_project_ids(user_id)),
        )

        if status is not None:
            statement = statement.where(Project.status == status)

        statement = statement.order_by(Project.created_at.desc())

        return list(self.db.scalars(statement).all())

    def get_for_user(
        self,
        project_id: int,
        user_id: int,
    ) -> Project | None:
        statement = select(Project).where(
            Project.id == project_id,
            Project.id.in_(accessible_project_ids(user_id)),
        )

        return self.db.scalar(statement)

    def search(
        self,
        user_id: int,
        query: str,
        limit: int = 20,
    ) -> list[Project]:
        pattern = f"%{query}%"

        statement = (
            select(Project)
            .where(
                Project.id.in_(accessible_project_ids(user_id)),
                or_(
                    Project.name.ilike(pattern),
                    Project.description.ilike(pattern),
                ),
            )
            .order_by(Project.updated_at.desc())
            .limit(limit)
        )

        return list(self.db.scalars(statement).all())

    def progress_map(
        self,
        project_ids: list[int],
    ) -> dict[int, tuple[int, int]]:
        """Возвращает {project_id: (всего задач, выполнено)}."""
        if not project_ids:
            return {}

        statement = (
            select(
                Task.project_id,
                func.count(Task.id),
                func.sum(case((Task.status == "done", 1), else_=0)),
            )
            .where(
                Task.project_id.in_(project_ids),
                Task.deleted_at.is_(None),
            )
            .group_by(Task.project_id)
        )

        return {
            project_id: (int(total or 0), int(done or 0))
            for project_id, total, done in self.db.execute(statement)
        }
