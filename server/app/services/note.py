from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ..core.errors import AppException
from ..models.note import Note
from ..repositories.note import NoteRepository
from ..repositories.project import ProjectRepository
from ..repositories.task import TaskRepository
from ..schemas.note import NoteCreate, NoteUpdate


class NoteService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.notes = NoteRepository(db)
        self.projects = ProjectRepository(db)
        self.tasks = TaskRepository(db)

    def list(
        self,
        user_id: int,
        project_id: int | None = None,
        task_id: int | None = None,
        search: str | None = None,
    ) -> list[Note]:
        return self.notes.list_for_user(
            user_id,
            project_id,
            task_id,
            search,
        )

    def get(
        self,
        note_id: int,
        user_id: int,
    ) -> Note:
        note = self.notes.get_for_user(note_id, user_id)

        if note is None:
            raise AppException(
                status_code=404,
                detail="Note not found",
                code="note_not_found",
            )

        return note

    def create(
        self,
        user_id: int,
        data: NoteCreate,
    ) -> Note:
        self._check_links(user_id, data.project_id, data.task_id)

        note = Note(
            user_id=user_id,
            project_id=data.project_id,
            task_id=data.task_id,
            title=data.title,
            content=data.content,
            is_pinned=data.is_pinned,
        )

        return self.notes.create(note)

    def update(
        self,
        note: Note,
        user_id: int,
        data: NoteUpdate,
    ) -> Note:
        changes = data.model_dump(exclude_unset=True)

        self._check_links(
            user_id,
            changes.get("project_id"),
            changes.get("task_id"),
        )

        for field, value in changes.items():
            setattr(note, field, value)

        self.db.flush()

        return note

    def soft_delete(self, note: Note) -> None:
        note.deleted_at = datetime.now(timezone.utc)

        self.db.flush()

    def _check_links(
        self,
        user_id: int,
        project_id: int | None,
        task_id: int | None,
    ) -> None:
        if project_id is not None:
            project = self.projects.get_for_user(project_id, user_id)

            if project is None:
                raise AppException(
                    status_code=404,
                    detail="Project not found",
                    code="project_not_found",
                )

        if task_id is not None:
            task = self.tasks.get_for_user(task_id, user_id)

            if task is None:
                raise AppException(
                    status_code=404,
                    detail="Task not found",
                    code="task_not_found",
                )
