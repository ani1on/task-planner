from datetime import datetime
from typing import Any

from client.api.client import ApiClient
from client.api.mapper import event_from_dict
from client.api.models import Event


def _iso(value: datetime | str | None) -> str | None:
    return value.isoformat() if isinstance(value, datetime) else value


class EventService:
    """Создание и получение календарных событий."""

    def __init__(self, api: ApiClient):
        self.api = api

    def list(
        self,
        date_from: datetime | str | None = None,
        date_to: datetime | str | None = None,
        project_id: int | None = None,
    ) -> list[Event]:
        params: dict[str, Any] = {}
        if date_from is not None:
            params["date_from"] = _iso(date_from)
        if date_to is not None:
            params["date_to"] = _iso(date_to)
        if project_id is not None:
            params["project_id"] = project_id

        response = self.api.get("/events", params=params) or []

        return [event_from_dict(item) for item in response]

    def get(self, event_id: int) -> Event:
        return event_from_dict(self.api.get(f"/events/{event_id}"))

    def create(self, **fields: Any) -> Event:
        payload = {
            key: _iso(value) if key in {"start_at", "end_at"} else value
            for key, value in fields.items()
        }

        return event_from_dict(self.api.post("/events", json=payload))

    def update(self, event_id: int, **fields: Any) -> Event:
        payload = {
            key: _iso(value) if key in {"start_at", "end_at"} else value
            for key, value in fields.items()
        }

        return event_from_dict(
            self.api.patch(f"/events/{event_id}", json=payload),
        )

    def delete(self, event_id: int) -> None:
        self.api.delete(f"/events/{event_id}")
