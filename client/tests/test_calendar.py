import calendar
import os
from datetime import date, datetime, timedelta

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import QDateTime
from PySide6.QtWidgets import QApplication, QDialog, QPushButton

from client.api.client import ApiClient
from client.api.errors import NotFoundError
from client.api.models import Event, Project, Task
from client.ui.dialogs.task import TaskDialog
from client.ui.dialogs.task_detail import RecurrenceSection
from client.ui.pages.calendar_page import CalendarPage, _EventEditor


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


def test_task_dialog_rejects_deadline_before_start(qapp):
    start = datetime.now().astimezone() + timedelta(days=2)
    due = start - timedelta(days=1)
    dialog = TaskDialog(
        projects=[Project(id=1, name="Проект")],
        due_at=due,
    )
    dialog.title_field.field.setText("Задача")
    dialog.start_check.setChecked(True)
    dialog.start_edit.setDateTime(QDateTime(start))

    dialog.accept()

    assert dialog.result() == QDialog.DialogCode.Rejected
    assert dialog.due_field.error.text()


def test_calendar_task_requires_deadline(qapp):
    dialog = TaskDialog(
        projects=[Project(id=1, name="Проект")],
        require_due_date=True,
    )
    dialog.title_field.field.setText("Задача")

    dialog.accept()

    assert dialog.result() == QDialog.DialogCode.Rejected
    assert dialog.due_field.error.text()


def test_calendar_adds_task_to_selected_day(qapp, monkeypatch):
    page = CalendarPage(api=ApiClient("http://127.0.0.1:1"))
    selected_day = min(12, page.today.day)
    opened = {}
    monkeypatch.setattr(
        page,
        "open_task_dialog",
        lambda **kwargs: opened.update(kwargs),
    )
    page._create_task_for_day(selected_day)

    assert opened["due_at"].date() == date(page.year, page.month, selected_day)
    assert opened["due_at"].hour == 9


def test_calendar_add_buttons_are_small_and_at_top_left(qapp):
    page = CalendarPage(api=ApiClient("http://127.0.0.1:1"))
    page.resize(1200, 850)
    page.show()
    qapp.processEvents()

    buttons = page.findChildren(QPushButton, "CalendarAddButton")
    assert len(buttons) == calendar.monthrange(page.year, page.month)[1]
    assert all(button.isVisible() for button in buttons)
    assert all(button.size().width() == button.size().height() == 28 for button in buttons)
    assert all(
        button.geometry().right() >= button.parentWidget().width() - 12
        for button in buttons
    )


def test_calendar_task_event_uses_priority_for_color(qapp):
    page = CalendarPage(api=ApiClient("http://127.0.0.1:1"))
    day = min(15, calendar.monthrange(page.year, page.month)[1])
    page._events = [{
        "id": 91,
        "kind": "task",
        "day": day,
        "month": page.month,
        "year": page.year,
        "title": "Критичная задача",
        "priority": "critical",
    }]

    cell = page._build_cell(day)
    task_button = cell.findChild(QPushButton, "CalendarTaskEvent")

    assert task_button is not None
    assert task_button.property("priority") == "critical"


def test_calendar_task_selection_opens_recurrence_from_task_date(qapp):
    page = CalendarPage(api=ApiClient("http://127.0.0.1:1"))
    due_at = datetime(
        page.year,
        page.month,
        min(15, calendar.monthrange(page.year, page.month)[1]),
        9,
    ).astimezone()
    task = Task(id=21, project_id=1, title="Повтор", due_at=due_at)

    class FakeTaskService:
        def recurrence(self, task_id):
            assert task_id == task.id
            raise NotFoundError("Повторение не найдено")

    page.task_service = FakeTaskService()
    page._task_models = {task.id: task}
    page._select_calendar_task(task.id)

    section = page.findChild(RecurrenceSection)
    assert section is not None
    assert section.start_at.dateTime().toPython().date() == due_at.date()
    assert section.end_at.dateTime().toPython().date() > due_at.date()
    assert section.day_of_month.value() == due_at.day


def test_calendar_event_editor_opens_without_shadowing_qt_event(qapp):
    page = CalendarPage(api=ApiClient("http://127.0.0.1:1"))
    start_at = datetime.now().astimezone()
    event = Event(
        id=91,
        title="Планирование",
        start_at=start_at,
        end_at=start_at + timedelta(hours=1),
    )
    page._event_models[event.id] = event
    page._selected_event_id = event.id

    page._render(page.year, page.month)

    editor = page.findChild(_EventEditor)
    assert editor is not None
    assert editor.title.text() == event.title
