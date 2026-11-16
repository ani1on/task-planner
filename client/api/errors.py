class ApiError(Exception):
    """Base API error."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        details=None,
    ):
        super().__init__(message)

        self.message = message
        self.status_code = status_code
        self.details = details


class NetworkError(ApiError):
    """Network/connection error."""


class UnauthorizedError(ApiError):
    """401 error."""


class ForbiddenError(ApiError):
    """403 error."""


class NotFoundError(ApiError):
    """404 error."""


class ValidationError(ApiError):
    """422 error."""


class ServerError(ApiError):
    """5xx error."""
