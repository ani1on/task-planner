from typing import Any

from client.api.client import ApiClient
from client.api.mapper import (
    checklist_from_dict,
    checklist_item_from_dict,
)
from client.api.models import Checklist, ChecklistItem


class ChecklistService:
    """Чек-листы задачи и их пункты."""

    def __init__(self, api: ApiClient):
        self.api = api

    def list(self, task_id: int) -> list[Checklist]:
        response = self.api.get("/checklists", params={"task_id": task_id}) or []

        return [checklist_from_dict(item) for item in response]

    def get(self, checklist_id: int) -> Checklist:
        response = self.api.get(f"/checklists/{checklist_id}")

        return checklist_from_dict(response)

    def create(self, task_id: int, title: str) -> Checklist:
        response = self.api.post(
            "/checklists",
            json={"task_id": task_id, "title": title},
        )

        return checklist_from_dict(response)

    def update(self, checklist_id: int, **fields: Any) -> Checklist:
        response = self.api.patch(
            f"/checklists/{checklist_id}",
            json=fields,
        )

        return checklist_from_dict(response)

    def delete(self, checklist_id: int) -> None:
        self.api.delete(f"/checklists/{checklist_id}")

    def items(self, checklist_id: int) -> list[ChecklistItem]:
        response = self.api.get(f"/checklists/{checklist_id}/items") or []

        return [checklist_item_from_dict(item) for item in response]

    def add_item(self, checklist_id: int, content: str) -> ChecklistItem:
        response = self.api.post(
            f"/checklists/{checklist_id}/items",
            json={"content": content},
        )

        return checklist_item_from_dict(response)

    def update_item(self, item_id: int, **fields: Any) -> ChecklistItem:
        response = self.api.patch(f"/checklist-items/{item_id}", json=fields)

        return checklist_item_from_dict(response)

    def delete_item(self, item_id: int) -> None:
        self.api.delete(f"/checklist-items/{item_id}")

    def list_with_items(
        self,
        task_id: int,
    ) -> list[tuple[Checklist, list[ChecklistItem]]]:
        """Чек-листы задачи вместе с пунктами (для диалога)."""
        result: list[tuple[Checklist, list[ChecklistItem]]] = []

        for checklist in self.list(task_id):
            result.append((checklist, self.items(checklist.id)))

        return result
