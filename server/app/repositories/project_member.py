from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..models.project_member import ProjectMember
from .base import BaseRepository


class ProjectMemberRepository(BaseRepository[ProjectMember]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, ProjectMember)

    def get(
        self,
        project_id: int,
        user_id: int,
    ) -> ProjectMember | None:
        statement = select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )

        return self.db.scalar(statement)

    def list_for_project(
        self,
        project_id: int,
    ) -> list[ProjectMember]:
        statement = (
            select(ProjectMember)
            .options(selectinload(ProjectMember.user))
            .where(ProjectMember.project_id == project_id)
            .order_by(ProjectMember.joined_at.asc())
        )

        return list(self.db.scalars(statement).all())

    def count_by_role(
        self,
        project_id: int,
        role: str,
    ) -> int:
        statement = select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.role == role,
        )

        return len(list(self.db.scalars(statement).all()))
