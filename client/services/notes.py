from typing import Any

from client.api.client import ApiClient
from client.api.mapper import note_from_dict
from client.api.models import Note


class NoteService:
    """Операции над заметками через REST API."""

    def __init__(self, api: ApiClient):
        self.api = api

    def list(
        self,
        project_id: int | None = None,
        task_id: int | None = None,
        search: str | None = None,
    ) -> list[Note]:
        params: dict[str, Any] = {}

        if project_id is not None:
            params["project_id"] = project_id

        if task_id is not None:
            params["task_id"] = task_id

        if search:
            params["search"] = search

        response = self.api.get("/notes", params=params) or []

        return [note_from_dict(item) for item in response]

    def get(self, note_id: int) -> Note:
        response = self.api.get(f"/notes/{note_id}")

        return note_from_dict(response)

    def create(
        self,
        title: str,
        content: str,
        project_id: int | None = None,
        task_id: int | None = None,
        is_pinned: bool = False,
    ) -> Note:
        response = self.api.post(
            "/notes",
            json={
                "title": title,
                "content": content,
                "project_id": project_id,
                "task_id": task_id,
                "is_pinned": is_pinned,
            },
        )

        return note_from_dict(response)

    def update(self, note_id: int, **fields: Any) -> Note:
        response = self.api.patch(f"/notes/{note_id}", json=fields)

        return note_from_dict(response)

    def delete(self, note_id: int) -> None:
        self.api.delete(f"/notes/{note_id}")
