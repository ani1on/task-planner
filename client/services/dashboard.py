from client.api.client import ApiClient
from client.api.mapper import dashboard_from_dict
from client.api.models import Dashboard


class DashboardService:
    """Сводка по задачам и проектам пользователя."""

    def __init__(self, api: ApiClient):
        self.api = api

    def get(self) -> Dashboard:
        response = self.api.get("/dashboard") or {}

        return dashboard_from_dict(response)
