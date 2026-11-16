from typing import Any

from client.api.client import ApiClient
from client.api.mapper import member_from_dict, project_from_dict
from client.api.models import Member, Project


class ProjectService:
    """Операции над проектами через REST API."""

    def __init__(self, api: ApiClient):
        self.api = api

    def list(self, status: str | None = None) -> list[Project]:
        params: dict[str, Any] = {}

        if status:
            params["status_filter"] = status

        response = self.api.get("/projects", params=params) or []

        return [project_from_dict(item) for item in response]

    def get(self, project_id: int) -> Project:
        response = self.api.get(f"/projects/{project_id}")

        return project_from_dict(response)

    def members(self, project_id: int) -> list[Member]:
        response = self.api.get(f"/projects/{project_id}/members") or []

        return [member_from_dict(item) for item in response]

    def list_with_members(
        self,
        status: str | None = None,
    ) -> list[tuple[Project, list[Member]]]:
        """Проекты вместе с участниками (для карточек)."""
        result: list[tuple[Project, list[Member]]] = []

        for project in self.list(status):
            try:
                members = self.members(project.id)
            except Exception:
                # Участники недоступны (например, нет прав) — карточка
                # всё равно должна отрисоваться.
                members = []

            result.append((project, members))

        return result

    def create(
        self,
        name: str,
        description: str | None = None,
        color: str = "blue",
    ) -> Project:
        response = self.api.post(
            "/projects",
            json={
                "name": name,
                "description": description,
                "color": color,
            },
        )

        return project_from_dict(response)

    def update(self, project_id: int, **fields: Any) -> Project:
        response = self.api.patch(f"/projects/{project_id}", json=fields)

        return project_from_dict(response)

    def archive(self, project_id: int) -> Project:
        response = self.api.post(f"/projects/{project_id}/archive")

        return project_from_dict(response)

    def delete(self, project_id: int) -> None:
        self.api.delete(f"/projects/{project_id}")
