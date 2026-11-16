from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..models.note import Note
from .base import BaseRepository


class NoteRepository(BaseRepository[Note]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Note)

    def list_for_user(
        self,
        user_id: int,
        project_id: int | None = None,
        task_id: int | None = None,
        search: str | None = None,
    ) -> list[Note]:
        statement = select(Note).where(
            Note.user_id == user_id,
            Note.deleted_at.is_(None),
        )

        if project_id is not None:
            statement = statement.where(Note.project_id == project_id)

        if task_id is not None:
            statement = statement.where(Note.task_id == task_id)

        if search:
            pattern = f"%{search}%"

            statement = statement.where(
                or_(
                    Note.title.ilike(pattern),
                    Note.content.ilike(pattern),
                )
            )

        statement = statement.order_by(
            Note.is_pinned.desc(),
            Note.updated_at.desc(),
        )

        return list(self.db.scalars(statement).all())

    def get_for_user(
        self,
        note_id: int,
        user_id: int,
    ) -> Note | None:
        statement = select(Note).where(
            Note.id == note_id,
            Note.user_id == user_id,
            Note.deleted_at.is_(None),
        )

        return self.db.scalar(statement)
