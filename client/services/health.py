from typing import Any

from client.api.client import ApiClient


class HealthService:
    """Диагностика доступности API и базы данных."""

    def __init__(self, api: ApiClient):
        self.api = api

    def status(self) -> dict[str, Any]:
        return self.api.get("/health")

    def database_status(self) -> dict[str, Any]:
        return self.api.get("/health/db")
