from datetime import datetime, timezone

import pytest

from client.services.activity import ActivityService
from client.services.checklists import ChecklistService
from client.services.comments import CommentService
from client.services.events import EventService
from client.services.health import HealthService
from client.services.notifications import NotificationService
from client.services.projects import ProjectService
from client.services.reminders import ReminderService
from client.services.tags import TagService
from client.services.tasks import TaskService


class FakeApi:
    def __init__(self, response=None):
        self.response = response
        self.calls = []

    def get(self, path, **kwargs):
        self.calls.append(("GET", path, kwargs))
        return self.response

    def post(self, path, **kwargs):
        self.calls.append(("POST", path, kwargs))
        return self.response

    def put(self, path, **kwargs):
        self.calls.append(("PUT", path, kwargs))
        return self.response

    def patch(self, path, **kwargs):
        self.calls.append(("PATCH", path, kwargs))
        return self.response

    def delete(self, path, **kwargs):
        self.calls.append(("DELETE", path, kwargs))
        return self.response


def test_event_service_uses_date_project_filters_and_crud():
    api = FakeApi({
        "id": 2,
        "title": "Планирование",
        "start_at": "2026-11-18T09:00:00+00:00",
        "end_at": "2026-11-18T10:00:00+00:00",
        "project_id": 7,
        "task_id": None,
        "all_day": False,
    })
    service = EventService(api)
    start = datetime(2026, 11, 1, tzinfo=timezone.utc)
    end = datetime(2026, 11, 30, tzinfo=timezone.utc)

    service.list(date_from=start, date_to=end, project_id=7)
    service.create(
        title="Планирование",
        start_at=start,
        end_at=end,
        project_id=7,
    )
    service.update(2, title="План")
    service.delete(2)

    assert api.calls == [
        (
            "GET",
            "/events",
            {
                "params": {
                    "date_from": start.isoformat(),
                    "date_to": end.isoformat(),
                    "project_id": 7,
                }
            },
        ),
        (
            "POST",
            "/events",
            {
                "json": {
                    "title": "Планирование",
                    "start_at": start.isoformat(),
                    "end_at": end.isoformat(),
                    "project_id": 7,
                }
            },
        ),
        ("PATCH", "/events/2", {"json": {"title": "План"}}),
        ("DELETE", "/events/2", {}),
    ]


def test_reminders_require_exactly_one_target_and_send_update_fields():
    response = {
        "id": 3,
        "remind_at": "2026-11-18T09:00:00+00:00",
        "channel": "desktop",
        "status": "pending",
        "task_id": 4,
        "event_id": None,
    }
    api = FakeApi(response)
    service = ReminderService(api)

    with pytest.raises(ValueError):
        service.create(datetime.now(timezone.utc))
    with pytest.raises(ValueError):
        service.create(
            datetime.now(timezone.utc),
            task_id=4,
            event_id=5,
        )

    service.create(datetime(2026, 11, 18, 9, tzinfo=timezone.utc), task_id=4)
    service.update(
        3,
        remind_at=datetime(2026, 11, 19, 9, tzinfo=timezone.utc),
        status="cancelled",
    )
    service.delete(3)

    assert api.calls[0] == (
        "POST",
        "/reminders",
        {
            "json": {
                "task_id": 4,
                "event_id": None,
                "remind_at": "2026-11-18T09:00:00+00:00",
                "channel": "desktop",
            }
        },
    )
    assert api.calls[1][0:2] == ("PATCH", "/reminders/3")
    assert api.calls[1][2]["json"]["status"] == "cancelled"
    assert api.calls[2][0:2] == ("DELETE", "/reminders/3")


def test_remaining_api_services_address_their_server_routes():
    api = FakeApi({
        "id": 1,
        "project_id": 8,
        "tasks_total": 5,
        "tasks_done": 2,
        "progress": 40,
        "name": "Tag",
        "color": "blue",
        "task_id": 9,
        "title": "Checklist",
        "position": 0,
        "author_id": 2,
        "content": "Comment",
    })

    assert ProjectService(api).progress(8)["progress"] == 40
    ProjectService(api).add_member(8, email="member@example.com", role="viewer")
    ProjectService(api).update_member_role(8, 3, "admin")
    ProjectService(api).remove_member(8, 3)
    TagService(api).get(1)
    TagService(api).update(1, name="Renamed")
    TagService(api).delete(1)
    ChecklistService(api).get(2)
    ChecklistService(api).update(2, title="Updated")
    CommentService(api).get(3)
    NotificationService(api).create("manual", "Title", "Message")
    NotificationService(api).delete(4)
    ActivityService(api).list(project_id=8, limit=10, offset=20)
    HealthService(api).status()
    HealthService(api).database_status()
    TaskService(api).recurrence(9)
    TaskService(api).set_recurrence(9, frequency="daily")
    TaskService(api).update_recurrence(9, is_active=False)
    TaskService(api).delete_recurrence(9)
    TaskService(api).create_next_occurrence(9)

    assert ("GET", "/projects/8/progress", {}) in api.calls
    assert ("POST", "/projects/8/members", {
        "json": {"role": "viewer", "email": "member@example.com"}
    }) in api.calls
    assert ("PATCH", "/tags/1", {"json": {"name": "Renamed"}}) in api.calls
    assert ("PATCH", "/checklists/2", {"json": {"title": "Updated"}}) in api.calls
    assert ("DELETE", "/notifications/4", {}) in api.calls
    assert ("GET", "/activity", {
        "params": {"limit": 10, "offset": 20, "project_id": 8}
    }) in api.calls
    assert ("GET", "/health/db", {}) in api.calls
    assert ("PUT", "/tasks/9/recurrence", {
        "json": {"frequency": "daily"}
    }) in api.calls
    assert ("POST", "/tasks/9/next-occurrence", {}) in api.calls
