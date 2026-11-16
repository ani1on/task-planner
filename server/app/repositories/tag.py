from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.tag import Tag
from .base import BaseRepository
from .project import accessible_project_ids


class TagRepository(BaseRepository[Tag]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Tag)

    def list_for_user(
        self,
        user_id: int,
        project_id: int | None = None,
    ) -> list[Tag]:
        statement = select(Tag).where(
            Tag.project_id.in_(accessible_project_ids(user_id)),
        )

        if project_id is not None:
            statement = statement.where(Tag.project_id == project_id)

        statement = statement.order_by(Tag.name.asc())

        return list(self.db.scalars(statement).all())

    def get_for_user(
        self,
        tag_id: int,
        user_id: int,
    ) -> Tag | None:
        statement = select(Tag).where(
            Tag.id == tag_id,
            Tag.project_id.in_(accessible_project_ids(user_id)),
        )

        return self.db.scalar(statement)

    def get_by_name(
        self,
        project_id: int,
        name: str,
    ) -> Tag | None:
        statement = select(Tag).where(
            Tag.project_id == project_id,
            Tag.name == name,
        )

        return self.db.scalar(statement)
