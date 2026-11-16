from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from server.main import app


def create_project(client: TestClient, name: str = "Тестовый проект") -> dict:
    response = client.post("/projects", json={"name": name})

    assert response.status_code == 201, response.text

    return response.json()


def create_task(
    client: TestClient,
    project_id: int,
    title: str = "Тестовая задача",
    **extra: object,
) -> dict:
    response = client.post(
        "/tasks",
        json={"project_id": project_id, "title": title, **extra},
    )

    assert response.status_code == 201, response.text

    return response.json()


def auth_token(client: TestClient) -> str:
    header = client.headers["Authorization"]

    return header.split(" ", 1)[1]


# ---------------------------------------------------------------------------
# Участники проекта и роли
# ---------------------------------------------------------------------------


def test_project_members_flow(
    auth_client: TestClient,
    other_client: TestClient,
) -> None:
    project = create_project(auth_client)
    other = other_client.get("/auth/me").json()

    members = auth_client.get(f"/projects/{project['id']}/members")

    assert members.status_code == 200
    assert [member["role"] for member in members.json()] == ["owner"]

    invited = auth_client.post(
        f"/projects/{project['id']}/members",
        json={"email": other["email"], "role": "viewer"},
    )

    assert invited.status_code == 201, invited.text
    assert invited.json()["user_id"] == other["id"]
    assert invited.json()["role"] == "viewer"

    duplicate = auth_client.post(
        f"/projects/{project['id']}/members",
        json={"email": other["email"]},
    )

    assert duplicate.status_code == 409
    assert duplicate.json()["code"] == "member_already_exists"

    # viewer видит проект, но не может создавать задачи.
    assert other_client.get(f"/projects/{project['id']}").status_code == 200

    forbidden = other_client.post(
        "/tasks",
        json={"project_id": project["id"], "title": "Нельзя"},
    )

    assert forbidden.status_code == 403
    assert forbidden.json()["code"] == "permission_denied"

    # Повышаем до member — создание задач разрешено.
    promoted = auth_client.patch(
        f"/projects/{project['id']}/members/{other['id']}",
        json={"role": "member"},
    )

    assert promoted.status_code == 200
    assert promoted.json()["role"] == "member"

    create_task(other_client, project["id"], "Задача участника")

    listed = auth_client.get(f"/projects/{project['id']}/members").json()

    assert len(listed) == 2

    removed = auth_client.delete(
        f"/projects/{project['id']}/members/{other['id']}",
    )

    assert removed.status_code == 200
    assert other_client.get(f"/projects/{project['id']}").status_code == 404


def test_membership_requires_admin(
    auth_client: TestClient,
    other_client: TestClient,
) -> None:
    project = create_project(auth_client)
    other = other_client.get("/auth/me").json()

    auth_client.post(
        f"/projects/{project['id']}/members",
        json={"email": other["email"], "role": "member"},
    )

    response = other_client.post(
        f"/projects/{project['id']}/members",
        json={"user_id": other["id"]},
    )

    assert response.status_code == 403


def test_owner_role_is_immutable(
    auth_client: TestClient,
) -> None:
    project = create_project(auth_client)
    owner_id = auth_client.get("/auth/me").json()["id"]

    response = auth_client.patch(
        f"/projects/{project['id']}/members/{owner_id}",
        json={"role": "member"},
    )

    assert response.status_code == 400
    assert response.json()["code"] == "owner_role_immutable"


# ---------------------------------------------------------------------------
# Подзадачи
# ---------------------------------------------------------------------------


def test_subtasks_flow(auth_client: TestClient) -> None:
    project = create_project(auth_client)
    task = create_task(auth_client, project["id"])

    first = auth_client.post(
        f"/tasks/{task['id']}/subtasks",
        json={"title": "Шаг 1"},
    )

    assert first.status_code == 201, first.text
    assert first.json()["parent_task_id"] == task["id"]

    second = auth_client.post(
        f"/tasks/{task['id']}/subtasks",
        json={"title": "Шаг 2", "status": "done"},
    )

    assert second.status_code == 201

    subtasks = auth_client.get(f"/tasks/{task['id']}/subtasks")

    assert subtasks.status_code == 200
    assert len(subtasks.json()) == 2

    progress = auth_client.get(f"/tasks/{task['id']}/subtasks/progress")

    assert progress.status_code == 200
    assert progress.json() == {"total": 2, "completed": 1}


# ---------------------------------------------------------------------------
# Теги задачи
# ---------------------------------------------------------------------------


def test_task_tags_flow(auth_client: TestClient) -> None:
    project = create_project(auth_client)
    task = create_task(auth_client, project["id"])

    tag = auth_client.post(
        "/tags",
        json={"project_id": project["id"], "name": "backend"},
    ).json()

    attached = auth_client.post(f"/tasks/{task['id']}/tags/{tag['id']}")

    assert attached.status_code == 200, attached.text
    assert [item["name"] for item in attached.json()] == ["backend"]

    duplicate = auth_client.post(f"/tasks/{task['id']}/tags/{tag['id']}")

    assert duplicate.status_code == 409

    fetched = auth_client.get(f"/tasks/{task['id']}").json()

    assert [item["id"] for item in fetched["tags"]] == [tag["id"]]

    filtered = auth_client.get(
        "/tasks",
        params={"project_id": project["id"], "tag_id": tag["id"]},
    )

    assert [item["id"] for item in filtered.json()] == [task["id"]]

    removed = auth_client.delete(f"/tasks/{task['id']}/tags/{tag['id']}")

    assert removed.status_code == 200
    assert auth_client.get(f"/tasks/{task['id']}/tags").json() == []


# ---------------------------------------------------------------------------
# Повторяющиеся задачи
# ---------------------------------------------------------------------------


def test_recurrence_flow(auth_client: TestClient) -> None:
    project = create_project(auth_client)
    task = create_task(auth_client, project["id"])

    assert (
        auth_client.get(f"/tasks/{task['id']}/recurrence").status_code == 404
    )

    start_at = datetime.now(timezone.utc)

    created = auth_client.put(
        f"/tasks/{task['id']}/recurrence",
        json={
            "frequency": "daily",
            "interval": 1,
            "start_at": start_at.isoformat(),
        },
    )

    assert created.status_code == 200, created.text
    assert created.json()["frequency"] == "daily"
    assert created.json()["next_run_at"] is not None

    updated = auth_client.patch(
        f"/tasks/{task['id']}/recurrence",
        json={"interval": 2},
    )

    assert updated.status_code == 200
    assert updated.json()["interval"] == 2

    next_task = auth_client.post(f"/tasks/{task['id']}/next-occurrence")

    assert next_task.status_code == 201, next_task.text
    assert next_task.json()["id"] != task["id"]
    assert next_task.json()["status"] == "todo"

    # Новая копия получила собственное правило повторения.
    assert (
        auth_client.get(f"/tasks/{next_task.json()['id']}/recurrence").status_code
        == 200
    )

    assert (
        auth_client.delete(f"/tasks/{next_task.json()['id']}/recurrence").status_code
        == 200
    )


def test_recurrence_requires_rule(auth_client: TestClient) -> None:
    project = create_project(auth_client)
    task = create_task(auth_client, project["id"])

    response = auth_client.post(f"/tasks/{task['id']}/next-occurrence")

    assert response.status_code == 400
    assert response.json()["code"] == "recurrence_not_available"


# ---------------------------------------------------------------------------
# Напоминания
# ---------------------------------------------------------------------------


def test_reminders_flow(auth_client: TestClient) -> None:
    project = create_project(auth_client)
    task = create_task(auth_client, project["id"])

    invalid = auth_client.post(
        "/reminders",
        json={"remind_at": datetime.now(timezone.utc).isoformat()},
    )

    assert invalid.status_code == 400
    assert invalid.json()["code"] == "reminder_target_required"

    future = datetime.now(timezone.utc) + timedelta(days=1)

    created = auth_client.post(
        "/reminders",
        json={
            "task_id": task["id"],
            "remind_at": future.isoformat(),
            "channel": "in_app",
        },
    )

    assert created.status_code == 201, created.text

    reminder = created.json()

    assert reminder["status"] == "pending"
    assert reminder["channel"] == "in_app"

    # Напоминание ещё не наступило.
    assert auth_client.post("/reminders/process-due").json()["processed"] == 0

    past = datetime.now(timezone.utc) - timedelta(minutes=5)

    updated = auth_client.patch(
        f"/reminders/{reminder['id']}",
        json={"remind_at": past.isoformat()},
    )

    assert updated.status_code == 200

    processed = auth_client.post("/reminders/process-due")

    assert processed.status_code == 200
    assert processed.json()["processed"] == 1

    sent = auth_client.get(f"/reminders/{reminder['id']}").json()

    assert sent["status"] == "sent"
    assert sent["sent_at"] is not None

    assert auth_client.get("/notifications/unread-count").json()["count"] == 1

    listed = auth_client.get("/reminders", params={"task_id": task["id"]}).json()

    assert [item["id"] for item in listed] == [reminder["id"]]

    assert auth_client.delete(f"/reminders/{reminder['id']}").status_code == 200
    assert auth_client.get(f"/reminders/{reminder['id']}").status_code == 404


# ---------------------------------------------------------------------------
# Dashboard и поиск
# ---------------------------------------------------------------------------


def test_dashboard(auth_client: TestClient) -> None:
    project = create_project(auth_client, "Dashboard проект")
    task = create_task(auth_client, project["id"], "Задача для dashboard")

    auth_client.patch(f"/tasks/{task['id']}", json={"status": "done"})

    response = auth_client.get("/dashboard")

    assert response.status_code == 200

    data = response.json()

    assert data["total_projects"] == 1
    assert data["stats"]["total"] == 1
    assert data["stats"]["done"] == 1
    assert data["projects"][0]["tasks_total"] == 1
    assert data["projects"][0]["tasks_done"] == 1
    assert data["projects"][0]["progress"] == 100


def test_project_progress(auth_client: TestClient) -> None:
    project = create_project(auth_client)

    first = create_task(auth_client, project["id"], "Первая")
    create_task(auth_client, project["id"], "Вторая")

    auth_client.patch(f"/tasks/{first['id']}", json={"status": "done"})

    response = auth_client.get(f"/projects/{project['id']}/progress")

    assert response.status_code == 200
    assert response.json() == {
        "project_id": project["id"],
        "tasks_total": 2,
        "tasks_done": 1,
        "progress": 50,
    }


def test_global_search(auth_client: TestClient) -> None:
    project = create_project(auth_client, "Космический проект")
    create_task(auth_client, project["id"], "Запустить ракету")

    auth_client.post(
        "/notes",
        json={"title": "Заметка о ракете", "content": "Топливо"},
    )

    response = auth_client.get("/search", params={"q": "ракет"})

    assert response.status_code == 200

    data = response.json()

    assert data["query"] == "ракет"
    assert any(task["title"] == "Запустить ракету" for task in data["tasks"])
    assert any("ракете" in note["title"] for note in data["notes"])
    assert data["projects"] == []

    by_project = auth_client.get("/search", params={"q": "Космический"})

    assert [item["id"] for item in by_project.json()["projects"]] == [project["id"]]


def test_search_requires_query(auth_client: TestClient) -> None:
    assert auth_client.get("/search").status_code == 422


# ---------------------------------------------------------------------------
# История активности и уведомления
# ---------------------------------------------------------------------------


def test_activity_log(auth_client: TestClient) -> None:
    project = create_project(auth_client, "Активный проект")
    task = create_task(auth_client, project["id"], "Задача с историей")

    response = auth_client.get(
        "/activity",
        params={"project_id": project["id"]},
    )

    assert response.status_code == 200

    actions = [entry["action"] for entry in response.json()]

    assert "task_created" in actions
    assert "project_created" in actions

    by_task = auth_client.get("/activity", params={"task_id": task["id"]}).json()

    assert all(entry["task_id"] == task["id"] for entry in by_task)


def test_assignment_notification(
    auth_client: TestClient,
    other_client: TestClient,
) -> None:
    project = create_project(auth_client)
    other = other_client.get("/auth/me").json()

    auth_client.post(
        f"/projects/{project['id']}/members",
        json={"user_id": other["id"], "role": "member"},
    )

    create_task(
        auth_client,
        project["id"],
        "Задача для другого",
        assignee_id=other["id"],
    )

    notifications = other_client.get("/notifications").json()

    assert any(
        item["type"] == "task_assigned" for item in notifications
    )


# ---------------------------------------------------------------------------
# Realtime
# ---------------------------------------------------------------------------


def test_websocket_ping(auth_client: TestClient) -> None:
    with auth_client.websocket_connect(
        f"/ws?token={auth_token(auth_client)}",
    ) as websocket:
        websocket.send_json({"action": "ping"})

        assert websocket.receive_json()["event"] == "pong"


def test_websocket_join_project(auth_client: TestClient) -> None:
    project = create_project(auth_client)

    with auth_client.websocket_connect(
        f"/ws?token={auth_token(auth_client)}",
    ) as websocket:
        websocket.send_json(
            {"action": "join_project", "project_id": project["id"]},
        )

        message = websocket.receive_json()

        assert message["event"] == "joined"
        assert message["payload"]["project_id"] == project["id"]

        websocket.send_json(
            {"action": "leave_project", "project_id": project["id"]},
        )

        assert websocket.receive_json()["event"] == "left"


def test_websocket_rejects_foreign_project(
    auth_client: TestClient,
    other_client: TestClient,
) -> None:
    project = create_project(auth_client)

    with other_client.websocket_connect(
        f"/ws?token={auth_token(other_client)}",
    ) as websocket:
        websocket.send_json(
            {"action": "join_project", "project_id": project["id"]},
        )

        message = websocket.receive_json()

        assert message["event"] == "error"
        assert message["payload"]["detail"] == "Project access denied"


def test_websocket_requires_valid_token() -> None:
    client = TestClient(app)

    with (
        pytest.raises(WebSocketDisconnect),
        client.websocket_connect("/ws?token=invalid") as websocket,
    ):
        websocket.receive_json()
