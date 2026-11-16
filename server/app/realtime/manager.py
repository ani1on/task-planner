import asyncio
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Хранит WebSocket-подключения по комнатам."""

    def __init__(self) -> None:
        self._rooms: dict[str, set[WebSocket]] = {}
        self._connections: dict[WebSocket, set[str]] = {}
        self._lock = asyncio.Lock()

    async def connect(
        self,
        websocket: WebSocket,
        room: str,
    ) -> None:
        await websocket.accept()

        async with self._lock:
            self._rooms.setdefault(room, set()).add(websocket)
            self._connections.setdefault(websocket, set()).add(room)

    async def join(
        self,
        websocket: WebSocket,
        room: str,
    ) -> None:
        async with self._lock:
            self._rooms.setdefault(room, set()).add(websocket)
            self._connections.setdefault(websocket, set()).add(room)

    async def leave(
        self,
        websocket: WebSocket,
        room: str,
    ) -> None:
        async with self._lock:
            self._remove_from_room(websocket, room)

    async def disconnect(
        self,
        websocket: WebSocket,
    ) -> None:
        async with self._lock:
            rooms = self._connections.pop(websocket, set())

            for room in list(rooms):
                self._remove_from_room(websocket, room)

    async def broadcast(
        self,
        room: str,
        message: dict[str, Any],
    ) -> None:
        connections = list(self._rooms.get(room, set()))

        for websocket in connections:
            try:
                await websocket.send_json(message)
            except Exception:
                logger.debug("Failed to send websocket message", exc_info=True)
                await self.disconnect(websocket)

    def room_size(self, room: str) -> int:
        return len(self._rooms.get(room, set()))

    def _remove_from_room(
        self,
        websocket: WebSocket,
        room: str,
    ) -> None:
        room_connections = self._rooms.get(room)

        if room_connections is not None:
            room_connections.discard(websocket)

            if not room_connections:
                self._rooms.pop(room, None)

        rooms = self._connections.get(websocket)

        if rooms is not None:
            rooms.discard(room)

            if not rooms:
                self._connections.pop(websocket, None)


manager = ConnectionManager()
