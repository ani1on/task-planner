from typing import Any


class AppException(Exception):
    def __init__(
        self,
        status_code: int,
        detail: str,
        code: str = "application_error",
        extra: dict[str, Any] | None = None,
    ) -> None:
        self.status_code = status_code
        self.detail = detail
        self.code = code
        self.extra = extra or {}

        super().__init__(detail)
