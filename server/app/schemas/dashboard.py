from pydantic import BaseModel

from .project import ProjectResponse
from .task import TaskResponse


class DashboardStats(BaseModel):
    total: int
    todo: int
    in_progress: int
    review: int
    done: int
    overdue: int
    due_today: int


class DashboardProject(BaseModel):
    id: int
    name: str
    color: str
    status: str
    progress: int
    tasks_total: int
    tasks_done: int


class DashboardResponse(BaseModel):
    stats: DashboardStats
    projects: list[DashboardProject]
    recent_projects: list[DashboardProject]
    upcoming_tasks: list[TaskResponse]
    recent_tasks: list[TaskResponse]
    total_projects: int


class ProjectProgressResponse(BaseModel):
    project_id: int
    tasks_total: int
    tasks_done: int
    progress: int


__all__ = [
    "DashboardProject",
    "DashboardResponse",
    "DashboardStats",
    "ProjectProgressResponse",
    "ProjectResponse",
]
