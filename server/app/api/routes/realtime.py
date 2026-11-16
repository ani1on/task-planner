import asyncio
import json

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from jose import JWTError

from ...core.security import decode_token
from ...database import SessionLocal
from ...realtime import manager, project_room, user_room
from ...repositories.user import UserRepository
from ...services.access import AccessService

router = APIRouter(tags=["Realtime"])


def _authenticate(token: str | None) -> int | None:
    if not token:
        return None

    try:
        payload = decode_token(token)
    except JWTError:
        return None

    if payload.get("type") != "access":
        return None

    subject = payload.get("sub")

    if subject is None:
        return None

    try:
        return int(subject)
    except (TypeError, ValueError):
        return None


def _user_exists(user_id: int) -> bool:
    db = SessionLocal()

    try:
        return UserRepository(db).get_by_id(user_id) is not None
    finally:
        db.close()


def _can_join_project(
    user_id: int,
    project_id: int,
) -> bool:
    db = SessionLocal()

    try:
        return AccessService(db).role(project_id, user_id) is not None
    finally:
        db.close()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str | None = Query(default=None),
) -> None:
    user_id = _authenticate(token)

    if user_id is None or not await asyncio.to_thread(_user_exists, user_id):
        await websocket.close(code=1008)
        return

    await manager.connect(websocket, user_room(user_id))

    try:
        while True:
            raw = await websocket.receive_text()

            try:
                message = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json(
                    {
                        "event": "error",
                        "payload": {"detail": "Invalid JSON"},
                    },
                )
                continue

            action = message.get("action")

            if action == "ping":
                await websocket.send_json({"event": "pong", "payload": {}})
                continue

            if action == "join_project":
                project_id = message.get("project_id")

                if isinstance(project_id, int) and await asyncio.to_thread(
                    _can_join_project,
                    user_id,
                    project_id,
                ):
                    await manager.join(
                        websocket,
                        project_room(project_id),
                    )
                    await websocket.send_json(
                        {
                            "event": "joined",
                            "payload": {"project_id": project_id},
                        },
                    )
                else:
                    await websocket.send_json(
                        {
                            "event": "error",
                            "payload": {"detail": "Project access denied"},
                        },
                    )

                continue

            if action == "leave_project":
                project_id = message.get("project_id")

                if isinstance(project_id, int):
                    await manager.leave(
                        websocket,
                        project_room(project_id),
                    )
                    await websocket.send_json(
                        {
                            "event": "left",
                            "payload": {"project_id": project_id},
                        },
                    )

                continue

            await websocket.send_json(
                {
                    "event": "error",
                    "payload": {"detail": "Unknown action"},
                },
            )
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(websocket)
