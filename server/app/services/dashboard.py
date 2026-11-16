from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from ..core.time import ensure_utc, utcnow
from ..models.project import Project
from ..models.task import Task
from ..repositories.project import ProjectRepository
from ..repositories.task import TaskRepository


class DashboardService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.tasks = TaskRepository(db)
        self.projects = ProjectRepository(db)

    def build(self, user_id: int) -> dict[str, Any]:
        tasks = self.tasks.list_for_user(user_id)
        projects = self.projects.list_for_user(user_id)

        progress = self.projects.progress_map([project.id for project in projects])

        dashboard_projects = [
            self._project(project, progress.get(project.id, (0, 0)))
            for project in projects
        ]

        now = utcnow()
        today = now.date()

        stats = {
            "total": len(tasks),
            "todo": 0,
            "in_progress": 0,
            "review": 0,
            "done": 0,
            "overdue": 0,
            "due_today": 0,
        }

        for task in tasks:
            if task.status in stats:
                stats[task.status] += 1

            if task.status == "done" or task.due_at is None:
                continue

            due_at = ensure_utc(task.due_at)

            if due_at < now:
                stats["overdue"] += 1

            if due_at.date() == today:
                stats["due_today"] += 1

        upcoming = sorted(
            (
                task
                for task in tasks
                if task.status != "done" and task.due_at is not None
            ),
            key=lambda task: ensure_utc(task.due_at),
        )[:5]

        recent_tasks = sorted(
            tasks,
            key=lambda task: ensure_utc(task.created_at),
            reverse=True,
        )[:5]

        return {
            "stats": stats,
            "projects": dashboard_projects,
            "recent_projects": dashboard_projects[:5],
            "upcoming_tasks": upcoming,
            "recent_tasks": recent_tasks,
            "total_projects": len(projects),
        }

    def project_progress(
        self,
        project_id: int,
    ) -> dict[str, int]:
        total, done = self.projects.progress_map([project_id]).get(
            project_id,
            (0, 0),
        )

        return {
            "project_id": project_id,
            "tasks_total": total,
            "tasks_done": done,
            "progress": int(done / total * 100) if total else 0,
        }

    def _project(
        self,
        project: Project,
        progress: tuple[int, int],
    ) -> dict[str, Any]:
        total, done = progress

        return {
            "id": project.id,
            "name": project.name,
            "color": project.color,
            "status": project.status,
            "progress": int(done / total * 100) if total else 0,
            "tasks_total": total,
            "tasks_done": done,
        }

    @staticmethod
    def due_at(task: Task) -> datetime | None:
        return task.due_at
