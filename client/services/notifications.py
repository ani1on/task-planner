from client.api.client import ApiClient
from client.api.mapper import notification_from_dict
from client.api.models import Notification


class NotificationService:
    def __init__(self, api: ApiClient):
        self.api = api

    def list(self, is_read: bool | None = None) -> list[Notification]:
        params = {}
        if is_read is not None:
            params["is_read"] = str(is_read).lower()
        response = self.api.get("/notifications", params=params) or []
        return [notification_from_dict(item) for item in response]

    def unread_count(self) -> int:
        response = self.api.get("/notifications/unread-count") or {}
        return int(response.get("count", 0))

    def mark_read(self, notification_id: int) -> Notification:
        response = self.api.post(f"/notifications/{notification_id}/read")
        return notification_from_dict(response)

    def mark_all_read(self) -> None:
        self.api.post("/notifications/read-all")

    def create(
        self,
        notification_type: str,
        title: str,
        message: str,
        task_id: int | None = None,
        project_id: int | None = None,
    ) -> Notification:
        response = self.api.post(
            "/notifications",
            json={
                "type": notification_type,
                "title": title,
                "message": message,
                "task_id": task_id,
                "project_id": project_id,
            },
        )

        return notification_from_dict(response)

    def delete(self, notification_id: int) -> None:
        self.api.delete(f"/notifications/{notification_id}")
