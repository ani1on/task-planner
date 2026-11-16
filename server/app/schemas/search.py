from pydantic import BaseModel

from .checklist import ChecklistResponse
from .note import NoteResponse
from .project import ProjectResponse
from .task import TaskResponse


class SearchResponse(BaseModel):
    query: str
    tasks: list[TaskResponse]
    projects: list[ProjectResponse]
    notes: list[NoteResponse]
    checklists: list[ChecklistResponse]
