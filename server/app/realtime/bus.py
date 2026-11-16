import asyncio
import logging
from typing import Any

from .manager import manager

logger = logging.getLogger(__name__)

_loop: asyncio.AbstractEventLoop | None = None


def set_event_loop(
    loop: asyncio.AbstractEventLoop | None,
) -> None:
    global _loop

    _loop = loop


def get_event_loop() -> asyncio.AbstractEventLoop | None:
    return _loop


def project_room(project_id: int) -> str:
    return f"project:{project_id}"


def user_room(user_id: int) -> str:
    return f"user:{user_id}"


def publish(
    room: str,
    event: str,
    payload: dict[str, Any],
) -> None:
    """Публикует событие в комнату, если приложение запущено с event loop."""
    loop = _loop

    if loop is None or loop.is_closed() or not loop.is_running():
        return

    message = {
        "event": event,
        "room": room,
        "payload": payload,
    }

    try:
        asyncio.run_coroutine_threadsafe(
            manager.broadcast(room, message),
            loop,
        )
    except RuntimeError:
        logger.debug("Realtime event loop is not available", exc_info=True)
