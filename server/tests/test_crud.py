from fastapi.testclient import TestClient

from server.main import app


def create_project(client: TestClient, name: str = "Тестовый проект") -> dict:
    response = client.post("/projects", json={"name": name})

    assert response.status_code == 201, response.text

    return response.json()


def create_task(
    client: TestClient,
    project_id: int,
    title: str = "Тестовая задача",
) -> dict:
    response = client.post(
        "/tasks",
        json={"project_id": project_id, "title": title},
    )

    assert response.status_code == 201, response.text

    return response.json()


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------


def test_projects_require_auth() -> None:
    client = TestClient(app)

    assert client.get("/projects").status_code in (401, 403)


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------


def test_project_crud(auth_client: TestClient) -> None:
    created = auth_client.post(
        "/projects",
        json={"name": "Диплом", "color": "violet"},
    )

    assert created.status_code == 201

    project = created.json()

    assert project["name"] == "Диплом"
    assert project["status"] == "active"

    listed = auth_client.get("/projects")

    assert listed.status_code == 200
    assert any(p["id"] == project["id"] for p in listed.json())

    fetched = auth_client.get(f"/projects/{project['id']}")

    assert fetched.status_code == 200

    updated = auth_client.patch(
        f"/projects/{project['id']}",
        json={"name": "Диплом v2"},
    )

    assert updated.status_code == 200
    assert updated.json()["name"] == "Диплом v2"
    assert updated.json()["color"] == "violet"

    archived = auth_client.post(f"/projects/{project['id']}/archive")

    assert archived.status_code == 200
    assert archived.json()["status"] == "archived"

    deleted = auth_client.delete(f"/projects/{project['id']}")

    assert deleted.status_code == 200
    assert auth_client.get(f"/projects/{project['id']}").status_code == 404


def test_project_not_found(auth_client: TestClient) -> None:
    response = auth_client.get("/projects/999999")

    assert response.status_code == 404
    assert response.json()["code"] == "project_not_found"


def test_project_isolation(
    auth_client: TestClient,
    other_client: TestClient,
) -> None:
    project = create_project(auth_client)

    assert other_client.get(f"/projects/{project['id']}").status_code == 404

    assert (
        other_client.patch(
            f"/projects/{project['id']}",
            json={"name": "hack"},
        ).status_code
        == 404
    )

    assert other_client.delete(f"/projects/{project['id']}").status_code == 404

    ids = [p["id"] for p in other_client.get("/projects").json()]

    assert project["id"] not in ids


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------


def test_task_crud(auth_client: TestClient) -> None:
    project = create_project(auth_client)

    created = auth_client.post(
        "/tasks",
        json={
            "project_id": project["id"],
            "title": "Сделать UI",
            "priority": "high",
        },
    )

    assert created.status_code == 201

    task = created.json()

    assert task["status"] == "todo"
    assert task["completed_at"] is None

    done = auth_client.patch(
        f"/tasks/{task['id']}",
        json={"status": "done"},
    )

    assert done.status_code == 200
    assert done.json()["completed_at"] is not None

    reopened = auth_client.patch(
        f"/tasks/{task['id']}",
        json={"status": "todo"},
    )

    assert reopened.json()["completed_at"] is None

    listed = auth_client.get(
        "/tasks",
        params={"project_id": project["id"]},
    )

    assert any(t["id"] == task["id"] for t in listed.json())

    deleted = auth_client.delete(f"/tasks/{task['id']}")

    assert deleted.status_code == 200
    assert auth_client.get(f"/tasks/{task['id']}").status_code == 404

    ids = [t["id"] for t in auth_client.get("/tasks").json()]

    assert task["id"] not in ids


def test_task_isolation(
    auth_client: TestClient,
    other_client: TestClient,
) -> None:
    project = create_project(auth_client)
    task = create_task(auth_client, project["id"])

    assert other_client.get(f"/tasks/{task['id']}").status_code == 404

    assert (
        other_client.patch(
            f"/tasks/{task['id']}",
            json={"title": "hack"},
        ).status_code
        == 404
    )

    response = other_client.post(
        "/tasks",
        json={"project_id": project["id"], "title": "x"},
    )

    assert response.status_code == 404
    assert response.json()["code"] == "project_not_found"


def test_invalid_status_returns_422(auth_client: TestClient) -> None:
    project = create_project(auth_client)

    response = auth_client.post(
        "/tasks",
        json={
            "project_id": project["id"],
            "title": "x",
            "status": "поехали",
        },
    )

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Tags
# ---------------------------------------------------------------------------


def test_tag_crud(auth_client: TestClient) -> None:
    project = create_project(auth_client)

    created = auth_client.post(
        "/tags",
        json={"project_id": project["id"], "name": "ui"},
    )

    assert created.status_code == 201

    tag = created.json()

    duplicate = auth_client.post(
        "/tags",
        json={"project_id": project["id"], "name": "ui"},
    )

    assert duplicate.status_code == 409
    assert duplicate.json()["code"] == "tag_already_exists"

    listed = auth_client.get(
        "/tags",
        params={"project_id": project["id"]},
    )

    assert any(t["id"] == tag["id"] for t in listed.json())

    updated = auth_client.patch(f"/tags/{tag['id']}", json={"color": "green"})

    assert updated.json()["color"] == "green"

    assert auth_client.delete(f"/tags/{tag['id']}").status_code == 200
    assert auth_client.get(f"/tags/{tag['id']}").status_code == 404


# ---------------------------------------------------------------------------
# Checklists
# ---------------------------------------------------------------------------


def test_checklist_with_items(auth_client: TestClient) -> None:
    project = create_project(auth_client)
    task = create_task(auth_client, project["id"])

    created = auth_client.post(
        "/checklists",
        json={"task_id": task["id"], "title": "Шаги"},
    )

    assert created.status_code == 201

    checklist = created.json()

    item = auth_client.post(
        f"/checklists/{checklist['id']}/items",
        json={"content": "Первый пункт"},
    )

    assert item.status_code == 201
    assert item.json()["is_completed"] is False

    item_id = item.json()["id"]

    toggled = auth_client.patch(
        f"/checklist-items/{item_id}",
        json={"is_completed": True},
    )

    assert toggled.status_code == 200
    assert toggled.json()["is_completed"] is True

    items = auth_client.get(f"/checklists/{checklist['id']}/items")

    assert len(items.json()) == 1

    assert auth_client.delete(f"/checklist-items/{item_id}").status_code == 200
    assert auth_client.delete(f"/checklists/{checklist['id']}").status_code == 200


def test_checklist_isolation(
    auth_client: TestClient,
    other_client: TestClient,
) -> None:
    project = create_project(auth_client)
    task = create_task(auth_client, project["id"])

    checklist = auth_client.post(
        "/checklists",
        json={"task_id": task["id"], "title": "X"},
    ).json()

    assert other_client.get(f"/checklists/{checklist['id']}").status_code == 404

    assert other_client.get(f"/checklists/{checklist['id']}/items").status_code == 404

    assert (
        other_client.post(
            f"/checklists/{checklist['id']}/items",
            json={"content": "x"},
        ).status_code
        == 404
    )


# ---------------------------------------------------------------------------
# Comments
# ---------------------------------------------------------------------------


def test_comment_crud(auth_client: TestClient) -> None:
    project = create_project(auth_client)
    task = create_task(auth_client, project["id"])

    created = auth_client.post(
        "/comments",
        json={"task_id": task["id"], "content": "Первый комментарий"},
    )

    assert created.status_code == 201

    comment = created.json()

    updated = auth_client.patch(
        f"/comments/{comment['id']}",
        json={"content": "Обновлено"},
    )

    assert updated.json()["content"] == "Обновлено"

    listed = auth_client.get(
        "/comments",
        params={"task_id": task["id"]},
    )

    assert len(listed.json()) == 1

    assert auth_client.delete(f"/comments/{comment['id']}").status_code == 200
    assert auth_client.get(f"/comments/{comment['id']}").status_code == 404


# ---------------------------------------------------------------------------
# Notes
# ---------------------------------------------------------------------------


def test_note_crud(auth_client: TestClient) -> None:
    created = auth_client.post(
        "/notes",
        json={"title": "Идея", "content": "Текст заметки"},
    )

    assert created.status_code == 201

    note = created.json()

    pinned = auth_client.patch(
        f"/notes/{note['id']}",
        json={"is_pinned": True},
    )

    assert pinned.json()["is_pinned"] is True

    assert any(n["id"] == note["id"] for n in auth_client.get("/notes").json())

    assert auth_client.delete(f"/notes/{note['id']}").status_code == 200
    assert auth_client.get(f"/notes/{note['id']}").status_code == 404


def test_note_foreign_project(
    auth_client: TestClient,
    other_client: TestClient,
) -> None:
    project = create_project(auth_client)

    response = other_client.post(
        "/notes",
        json={
            "title": "x",
            "content": "y",
            "project_id": project["id"],
        },
    )

    assert response.status_code == 404
    assert response.json()["code"] == "project_not_found"


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------


def test_event_crud(auth_client: TestClient) -> None:
    created = auth_client.post(
        "/events",
        json={
            "title": "Созвон",
            "start_at": "2030-01-01T10:00:00Z",
            "end_at": "2030-01-01T11:00:00Z",
        },
    )

    assert created.status_code == 201

    event = created.json()

    listed = auth_client.get("/events")

    assert any(e["id"] == event["id"] for e in listed.json())

    updated = auth_client.patch(
        f"/events/{event['id']}",
        json={"title": "Созвон v2"},
    )

    assert updated.json()["title"] == "Созвон v2"

    assert auth_client.delete(f"/events/{event['id']}").status_code == 200
    assert auth_client.get(f"/events/{event['id']}").status_code == 404


def test_event_invalid_time(auth_client: TestClient) -> None:
    response = auth_client.post(
        "/events",
        json={
            "title": "Bad",
            "start_at": "2030-01-01T11:00:00Z",
            "end_at": "2030-01-01T10:00:00Z",
        },
    )

    assert response.status_code == 400
    assert response.json()["code"] == "invalid_event_time"


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------


def test_notification_flow(auth_client: TestClient) -> None:
    created = auth_client.post(
        "/notifications",
        json={
            "type": "task_assigned",
            "title": "Вам назначена задача",
            "message": "Сделать UI",
        },
    )

    assert created.status_code == 201

    notification = created.json()

    assert notification["is_read"] is False

    count = auth_client.get("/notifications/unread-count").json()["count"]

    assert count == 1

    read = auth_client.post(f"/notifications/{notification['id']}/read")

    assert read.status_code == 200
    assert read.json()["is_read"] is True

    assert auth_client.get("/notifications/unread-count").json()["count"] == 0

    auth_client.post(
        "/notifications",
        json={"type": "comment", "title": "t", "message": "m"},
    )

    assert auth_client.post("/notifications/read-all").status_code == 200
    assert auth_client.get("/notifications/unread-count").json()["count"] == 0


# ---------------------------------------------------------------------------
# Profile & Settings
# ---------------------------------------------------------------------------


def test_update_profile(auth_client: TestClient) -> None:
    response = auth_client.patch("/users/me", json={"nick_name": "new_nick"})

    assert response.status_code == 200
    assert response.json()["nick_name"] == "new_nick"

    assert auth_client.get("/auth/me").json()["nick_name"] == "new_nick"


def test_update_profile_duplicate_nickname(
    auth_client: TestClient,
    other_client: TestClient,
) -> None:
    other_nick_name = other_client.get("/auth/me").json()["nick_name"]

    response = auth_client.patch(
        "/users/me",
        json={"nick_name": other_nick_name},
    )

    assert response.status_code == 409
    assert response.json()["code"] == "nickname_already_exists"


def test_settings_flow(auth_client: TestClient) -> None:
    fetched = auth_client.get("/users/me/settings")

    assert fetched.status_code == 200
    assert fetched.json()["theme"] in ("light", "dark")

    updated = auth_client.patch(
        "/users/me/settings",
        json={"theme": "dark", "notification_enabled": False},
    )

    assert updated.status_code == 200
    assert updated.json()["theme"] == "dark"
    assert updated.json()["notification_enabled"] is False

    again = auth_client.get("/users/me/settings")

    assert again.json()["theme"] == "dark"
    assert again.json()["notification_enabled"] is False


def test_settings_invalid_theme(auth_client: TestClient) -> None:
    response = auth_client.patch("/users/me/settings", json={"theme": "neon"})

    assert response.status_code == 422
