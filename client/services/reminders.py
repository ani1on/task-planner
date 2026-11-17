from datetime import datetime
from typing import Any

from client.api.client import ApiClient
from client.api.mapper import reminder_from_dict
from client.api.models import Reminder


def _iso(value: datetime | str) -> str:
    return value.isoformat() if isinstance(value, datetime) else value


class ReminderService:
    """Работа с напоминаниями, привязанными к задачам и событиям."""

    def __init__(self, api: ApiClient):
        self.api = api

    def list(
        self,
        status: str | None = None,
        task_id: int | None = None,
        event_id: int | None = None,
    ) -> list[Reminder]:
        params: dict[str, Any] = {}
        if status is not None:
            params["status_filter"] = status
        if task_id is not None:
            params["task_id"] = task_id
        if event_id is not None:
            params["event_id"] = event_id

        response = self.api.get("/reminders", params=params) or []

        return [reminder_from_dict(item) for item in response]

    def get(self, reminder_id: int) -> Reminder:
        return reminder_from_dict(self.api.get(f"/reminders/{reminder_id}"))

    def create(
        self,
        remind_at: datetime | str,
        *,
        task_id: int | None = None,
        event_id: int | None = None,
        channel: str = "desktop",
    ) -> Reminder:
        if (task_id is None) == (event_id is None):
            raise ValueError("Напоминание должно быть связано с задачей или событием")

        return reminder_from_dict(
            self.api.post(
                "/reminders",
                json={
                    "task_id": task_id,
                    "event_id": event_id,
                    "remind_at": _iso(remind_at),
                    "channel": channel,
                },
            ),
        )

    def update(self, reminder_id: int, **fields: Any) -> Reminder:
        if isinstance(fields.get("remind_at"), datetime):
            fields["remind_at"] = _iso(fields["remind_at"])

        return reminder_from_dict(
            self.api.patch(f"/reminders/{reminder_id}", json=fields),
        )

    def delete(self, reminder_id: int) -> None:
        self.api.delete(f"/reminders/{reminder_id}")
