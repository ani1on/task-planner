import threading
from typing import Any

import requests

from .errors import (
    ApiError,
    ForbiddenError,
    NetworkError,
    NotFoundError,
    ServerError,
    UnauthorizedError,
    ValidationError,
)


class ApiClient:
    def __init__(
        self,
        base_url: str,
        timeout: int = 10,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        self.session = requests.Session()

        # Запросы выполняются и из GUI-потока, и из QThreadPool,
        # а requests.Session не гарантирует потокобезопасность.
        self._lock = threading.Lock()

    def set_token(self, token: str | None):
        if token:
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        else:
            self.session.headers.pop("Authorization", None)

    def get(self, path: str, **kwargs):
        return self._request("GET", path, **kwargs)

    def post(self, path: str, **kwargs):
        return self._request("POST", path, **kwargs)

    def put(self, path: str, **kwargs):
        return self._request("PUT", path, **kwargs)

    def patch(self, path: str, **kwargs):
        return self._request("PATCH", path, **kwargs)

    def delete(self, path: str, **kwargs):
        return self._request("DELETE", path, **kwargs)

    def _request(
        self,
        method: str,
        path: str,
        **kwargs,
    ) -> Any:
        url = f"{self.base_url}/{path.lstrip('/')}"

        try:
            with self._lock:
                response = self.session.request(
                    method,
                    url,
                    timeout=self.timeout,
                    **kwargs,
                )
        except requests.RequestException as exc:
            raise NetworkError("Не удалось подключиться к серверу") from exc

        if response.ok:
            if not response.content:
                return None

            return response.json()

        self._handle_error(response)

    def _handle_error(self, response):
        try:
            data = response.json()
        except ValueError:
            data = None

        message = "Ошибка сервера"

        if isinstance(data, dict):
            message = data.get("detail", message)

        status = response.status_code

        if status == 401:
            raise UnauthorizedError(message, status, data)

        if status == 403:
            raise ForbiddenError(message, status, data)

        if status == 404:
            raise NotFoundError(message, status, data)

        if status == 422:
            raise ValidationError(message, status, data)

        if status >= 500:
            raise ServerError(message, status, data)

        raise ApiError(message, status, data)
