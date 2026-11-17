from typing import Any

from client.api.client import ApiClient
from client.api.mapper import recurrence_from_dict, task_from_dict
from client.api.models import Recurrence, Task


class TaskService:
    """Операции над задачами через REST API."""

    def __init__(self, api: ApiClient):
        self.api = api

    def list(
        self,
        project_id: int | None = None,
        status: str | None = None,
        priority: str | None = None,
        assignee_id: int | None = None,
        tag_id: int | None = None,
        search: str | None = None,
    ) -> list[Task]:
        params: dict[str, Any] = {}

        if project_id is not None:
            params["project_id"] = project_id

        if status:
            params["status_filter"] = status

        if priority:
            params["priority"] = priority

        if assignee_id is not None:
            params["assignee_id"] = assignee_id

        if tag_id is not None:
            params["tag_id"] = tag_id

        if search:
            params["search"] = search

        response = self.api.get("/tasks", params=params) or []

        return [task_from_dict(item) for item in response]

    def get(self, task_id: int) -> Task:
        response = self.api.get(f"/tasks/{task_id}")

        return task_from_dict(response)

    def create(
        self,
        project_id: int,
        title: str,
        description: str | None = None,
        status: str = "todo",
        priority: str = "medium",
        parent_task_id: int | None = None,
        assignee_id: int | None = None,
        start_at: str | None = None,
        due_at: str | None = None,
        position: int = 0,
    ) -> Task:
        response = self.api.post(
            "/tasks",
            json={
                "project_id": project_id,
                "title": title,
                "description": description,
                "status": status,
                "priority": priority,
                "parent_task_id": parent_task_id,
                "assignee_id": assignee_id,
                "start_at": start_at,
                "due_at": due_at,
                "position": position,
            },
        )

        return task_from_dict(response)

    def update(self, task_id: int, **fields: Any) -> Task:
        response = self.api.patch(f"/tasks/{task_id}", json=fields)

        return task_from_dict(response)

    def delete(self, task_id: int) -> None:
        self.api.delete(f"/tasks/{task_id}")

    def subtasks(self, task_id: int) -> list[Task]:
        response = self.api.get(f"/tasks/{task_id}/subtasks") or []

        return [task_from_dict(item) for item in response]

    def create_subtask(self, task_id: int, title: str) -> Task:
        response = self.api.post(
            f"/tasks/{task_id}/subtasks",
            json={"title": title},
        )

        return task_from_dict(response)

    def subtask_progress(self, task_id: int) -> dict[str, int]:
        return self.api.get(f"/tasks/{task_id}/subtasks/progress") or {
            "total": 0,
            "completed": 0,
        }

    def recurrence(self, task_id: int) -> Recurrence:
        response = self.api.get(f"/tasks/{task_id}/recurrence")

        return recurrence_from_dict(response)

    def set_recurrence(self, task_id: int, **fields: Any) -> Recurrence:
        response = self.api.put(
            f"/tasks/{task_id}/recurrence",
            json=fields,
        )

        return recurrence_from_dict(response)

    def update_recurrence(self, task_id: int, **fields: Any) -> Recurrence:
        response = self.api.patch(
            f"/tasks/{task_id}/recurrence",
            json=fields,
        )

        return recurrence_from_dict(response)

    def delete_recurrence(self, task_id: int) -> None:
        self.api.delete(f"/tasks/{task_id}/recurrence")

    def create_next_occurrence(self, task_id: int) -> Task:
        response = self.api.post(f"/tasks/{task_id}/next-occurrence")

        return task_from_dict(response)
