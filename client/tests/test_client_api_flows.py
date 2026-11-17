import os
from datetime import date, datetime, timedelta

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QDateTime
from PySide6.QtWidgets import QApplication, QDialog, QLabel

from client.api.client import ApiClient
from client.api.models import Member, Project
from client.services.auth import AuthService
from client.themes.manager import ThemeManager
from client.ui.components.task_card import TaskCard
from client.ui.crud_actions import TaskActionsMixin
from client.ui.dialogs.event import EventDialog
from client.ui.dialogs.recurrence import RecurrenceDialog
from client.ui.dialogs.reset_password import ResetPasswordDialog
from client.ui.main_window import MainWindow
from client.ui.pages.calendar_page import CalendarPage


def _app():
    return QApplication.instance() or QApplication([])


def test_event_dialog_validates_time_order():
    _app()
    start = datetime.now().astimezone() + timedelta(days=1)
    dialog = EventDialog(
        [Project(id=1, name="Проект")],
        start_at=start,
    )
    dialog.title_input.setText("Встреча")
    dialog.end_edit.setDateTime(QDateTime(start - timedelta(hours=1)))

    dialog.accept()

    assert dialog.result() == QDialog.DialogCode.Rejected
    assert dialog.end_field.error.text()


def test_calendar_creates_event_for_selected_day(monkeypatch):
    _app()
    page = CalendarPage(api=ApiClient("http://127.0.0.1:1"))
    selected_day = date(page.year, page.month, min(12, page.today.day))
    created = {}

    class FakeEventService:
        def create(self, **payload):
            created.update(payload)

    page.event_service = FakeEventService()
    monkeypatch.setattr(page, "reload", lambda: None)

    def accept_event(dialog):
        dialog.title_input.setText("Событие календаря")
        dialog.accept()
        return dialog.result()

    monkeypatch.setattr(EventDialog, "exec", accept_event)
    page._create_event_for_day(selected_day)

    assert created["title"] == "Событие календаря"
    assert datetime.fromisoformat(created["start_at"]).date() == selected_day


def test_weekly_recurrence_requires_at_least_one_day():
    _app()
    dialog = RecurrenceDialog()
    dialog.frequency.setCurrentIndex(dialog.frequency.findData("weekly"))
    dialog.accept()

    assert dialog.result() == QDialog.DialogCode.Rejected
    dialog.days[0].setChecked(True)
    dialog.accept()

    assert dialog.result() == QDialog.DialogCode.Accepted
    assert dialog.payload()["days_of_week"] == [1]


def test_reset_password_dialog_validates_token_and_matching_passwords():
    _app()
    dialog = ResetPasswordDialog()
    dialog.token.setText("token")
    dialog.password.setText("password123")
    dialog.confirm.setText("different")

    dialog.accept()

    assert dialog.result() == QDialog.DialogCode.Rejected
    assert dialog.confirm_field.error.text()

    dialog.confirm.setText("password123")
    dialog.accept()

    assert dialog.result() == QDialog.DialogCode.Accepted
    assert dialog.values() == ("token", "password123")


def test_main_window_registers_activity_page_without_network_calls(monkeypatch):
    app = _app()

    class FakeApi:
        base_url = "http://127.0.0.1:1"

        def get(self, path, params=None):
            if path == "/notifications":
                return []
            if path == "/notifications/unread-count":
                return {"count": 0}
            raise AssertionError(f"Unexpected GET {path}")

    api = FakeApi()
    auth = AuthService(api)
    auth.user = {"id": 1, "nick_name": "User", "email": "user@example.com"}
    monkeypatch.setattr(MainWindow, "navigate_to", lambda self, _key: None)

    window = MainWindow(
        api,
        auth,
        ThemeManager(app),
    )

    assert "activity" in window.pages
    assert "activity" in window.sidebar.buttons


def test_task_comment_shows_author_nickname():
    app = _app()

    class FakeApi:
        def get(self, path, params=None):
            assert path == "/comments"
            return [{
                "id": 3,
                "task_id": 8,
                "author_id": 5,
                "content": "Комментарий",
            }]

    class FakeProjectService:
        def members(self, project_id):
            assert project_id == 2
            return [
                Member(
                    id=1,
                    project_id=2,
                    user_id=5,
                    role="member",
                    nick_name="Автор",
                )
            ]

    class Actions(TaskActionsMixin):
        pass

    card = TaskCard({
        "id": 8,
        "project_id": 2,
        "title": "Задача",
    })
    page = Actions()
    page.api = FakeApi()
    page.task_service = object()
    page.project_service = FakeProjectService()
    page.user_id = 1
    page._task_cards = {8: card}

    page.open_task_panel(8, "comments")
    app.processEvents()

    labels = [label.text() for label in card.findChildren(QLabel)]
    assert "Автор" in labels
