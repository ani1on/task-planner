from typing import Any

from sqlalchemy.orm import Session

from ..repositories.checklist import ChecklistRepository
from ..repositories.note import NoteRepository
from ..repositories.project import ProjectRepository
from ..repositories.task import TaskRepository


class SearchService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.tasks = TaskRepository(db)
        self.projects = ProjectRepository(db)
        self.notes = NoteRepository(db)
        self.checklists = ChecklistRepository(db)

    def search(
        self,
        user_id: int,
        query: str,
        limit: int = 20,
    ) -> dict[str, Any]:
        query = query.strip()

        if not query:
            return {
                "query": query,
                "tasks": [],
                "projects": [],
                "notes": [],
                "checklists": [],
            }

        return {
            "query": query,
            "tasks": self.tasks.search(user_id, query, limit),
            "projects": self.projects.search(user_id, query, limit),
            "notes": self.notes.list_for_user(user_id, search=query)[:limit],
            "checklists": self.checklists.search(user_id, query, limit),
        }
