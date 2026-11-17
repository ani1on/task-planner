from typing import Any

from client.api.client import ApiClient
from client.api.mapper import activity_from_dict
from client.api.models import Activity


class ActivityService:
    """Журнал действий пользователя."""

    def __init__(self, api: ApiClient):
        self.api = api

    def list(
        self,
        project_id: int | None = None,
        task_id: int | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Activity]:
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if project_id is not None:
            params["project_id"] = project_id
        if task_id is not None:
            params["task_id"] = task_id

        response = self.api.get("/activity", params=params) or []

        return [activity_from_dict(item) for item in response]
