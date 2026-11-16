import threading
import time
from collections import defaultdict
from collections.abc import Callable

from fastapi import Request

from ..config import settings
from .errors import AppException


class RateLimiter:
    """Простой in-memory rate limiter со скользящим окном."""

    def __init__(
        self,
        limit: int,
        window_seconds: int,
    ) -> None:
        self.limit = limit
        self.window_seconds = window_seconds

        self._hits: dict[str, list[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def hit(self, key: str) -> None:
        now = time.monotonic()

        with self._lock:
            hits = [
                timestamp
                for timestamp in self._hits[key]
                if now - timestamp < self.window_seconds
            ]

            if len(hits) >= self.limit:
                self._hits[key] = hits

                raise AppException(
                    status_code=429,
                    detail="Too many requests, try again later",
                    code="rate_limit_exceeded",
                )

            hits.append(now)
            self._hits[key] = hits

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


_limiter: RateLimiter | None = None


def get_limiter() -> RateLimiter:
    global _limiter

    if (
        _limiter is None
        or _limiter.limit != settings.rate_limit_requests
        or _limiter.window_seconds != settings.rate_limit_window_seconds
    ):
        _limiter = RateLimiter(
            limit=settings.rate_limit_requests,
            window_seconds=settings.rate_limit_window_seconds,
        )

    return _limiter


def reset_limiter() -> None:
    if _limiter is not None:
        _limiter.reset()


def _client_key(
    request: Request,
    scope: str,
) -> str:
    host = request.client.host if request.client else "unknown"

    return f"{scope}:{host}"


def rate_limit(scope: str) -> Callable[[Request], None]:
    """Возвращает FastAPI-зависимость для ограничения запросов."""

    def dependency(request: Request) -> None:
        if not settings.rate_limit_enabled:
            return

        get_limiter().hit(_client_key(request, scope))

    return dependency
