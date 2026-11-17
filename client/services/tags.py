from typing import Any

from client.api.client import ApiClient
from client.api.mapper import tag_from_dict
from client.api.models import Tag


class TagService:
    """Операции над тегами и тегами задач."""

    def __init__(self, api: ApiClient):
        self.api = api

    def list(self, project_id: int | None = None) -> list[Tag]:
        params = {}

        if project_id is not None:
            params["project_id"] = project_id

        response = self.api.get("/tags", params=params) or []

        return [tag_from_dict(item) for item in response]

    def create(
        self,
        project_id: int,
        name: str,
        color: str = "blue",
    ) -> Tag:
        response = self.api.post(
            "/tags",
            json={
                "project_id": project_id,
                "name": name,
                "color": color,
            },
        )

        return tag_from_dict(response)

    def get(self, tag_id: int) -> Tag:
        response = self.api.get(f"/tags/{tag_id}")

        return tag_from_dict(response)

    def update(self, tag_id: int, **fields: Any) -> Tag:
        response = self.api.patch(f"/tags/{tag_id}", json=fields)

        return tag_from_dict(response)

    def delete(self, tag_id: int) -> None:
        self.api.delete(f"/tags/{tag_id}")

    def task_tags(self, task_id: int) -> list[Tag]:
        response = self.api.get(f"/tasks/{task_id}/tags") or []

        return [tag_from_dict(item) for item in response]

    def add_to_task(self, task_id: int, tag_id: int) -> list[Tag]:
        response = self.api.post(f"/tasks/{task_id}/tags/{tag_id}") or []

        return [tag_from_dict(item) for item in response]

    def remove_from_task(self, task_id: int, tag_id: int) -> None:
        self.api.delete(f"/tasks/{task_id}/tags/{tag_id}")
