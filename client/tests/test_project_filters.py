import calendar
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication, QPushButton

from client.api.client import ApiClient
from client.api.models import Project, Task
from client.ui.components.project_card import ProjectCard
from client.ui.components.task_card import TaskCard
from client.ui.pages.calendar_page import CalendarPage
from client.ui.pages.dashboard_page import DashboardPage
from client.ui.pages.notes_page import NotesPage
from client.ui.pages.projects_page import ProjectsPage
from client.ui.pages.tasks_page import TasksPage


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


def _api():
    return ApiClient("http://127.0.0.1:1")


def _projects():
    return [
        {
            "id": 1,
            "name": "Task Planner",
            "description": "Планировщик задач",
            "color": "blue",
            "status": "active",
            "done": 0,
            "total": 0,
            "members": [],
        },
        {
            "id": 2,
            "name": "Документация",
            "description": "Описание схемы данных",
            "color": "purple",
            "status": "active",
            "done": 0,
            "total": 0,
            "members": [],
        },
        {
            "id": 3,
            "name": "Инфраструктура",
            "description": "Настройка CI",
            "color": "teal",
            "status": "active",
            "done": 0,
            "total": 0,
            "members": [],
        },
    ]


def _tasks():
    tasks = [
        ("Собрать каркас интерфейса", 1, "in_progress", "high", ["ui"]),
        ("Продумать схему базы данных", 1, "done", "medium", ["backend"]),
        ("Подключить авторизацию", 1, "review", "critical", ["auth"]),
        ("Описать REST API задач", 2, "todo", "low", ["docs"]),
        ("Настроить CI для тестов", 3, "todo", "medium", ["ci"]),
    ]
    return [
        {
            "id": task_id,
            "title": title,
            "project_id": project_id,
            "project": next(
                project["name"] for project in _projects()
                if project["id"] == project_id
            ),
            "description": "",
            "status": status,
            "priority": priority,
            "due": "",
            "due_at": None,
            "tags": tags,
            "tag_colors": {},
            "done": status == "done",
            "has_subtasks": False,
        }
        for task_id, (title, project_id, status, priority, tags)
        in enumerate(tasks, start=1)
    ]


def test_tasks_page_filters_project_and_shows_all(qapp):
    page = TasksPage(api=_api())
    page._set_tasks({
        "views": _tasks(),
        "models": {},
        "projects": _projects(),
    })
    assert {task["id"] for task in page.all_tasks} == {1, 2, 3, 4, 5}

    page.project_combo.setCurrentIndex(page.project_combo.findData(2))
    assert {card.task["id"] for card in page._task_cards.values()} == {4}

    page.project_combo.setCurrentIndex(0)
    assert {card.task["id"] for card in page._task_cards.values()} == {
        1, 2, 3, 4, 5
    }


def test_dashboard_task_cards_cannot_be_edited(qapp):
    page = DashboardPage(api=_api())
    page.content_layout.addLayout(page._build_today(_tasks()[:3]))
    card = next(iter(page._task_cards.values()))

    assert card.more_button.isHidden()
    assert all(button.isHidden() for button in card.panel_buttons.values())

    card.activated.emit(card._task_id())
    card.toggle_editor()

    assert card.editor.isHidden()


def test_tasks_page_searches_and_filters_by_tag(qapp):
    page = TasksPage(api=_api())
    page._set_tasks({
        "views": _tasks(),
        "models": {},
        "projects": _projects(),
    })

    page.tag_combo.setCurrentIndex(page.tag_combo.findData("ui"))
    assert set(page._task_cards) == {1}

    page.tag_combo.setCurrentIndex(0)
    page.search_input.setText("REST")
    assert set(page._task_cards) == {4}


def test_projects_page_searches_by_name_and_description(qapp):
    page = ProjectsPage(api=_api())
    page._render({"views": _projects(), "models": {}})

    page.search_input.setText("схемы данных")
    assert set(page._project_cards) == {2}


def test_project_card_keeps_status_dropdown_without_archive_or_progress_buttons(qapp):
    card = ProjectCard({
        "id": 1,
        "name": "Проект",
        "status": "active",
    })

    assert card.status_combo.findData("archived") >= 0
    button_texts = [button.text().casefold() for button in card.findChildren(QPushButton)]
    assert not any("архив" in text or "прогресс" in text for text in button_texts)


def test_task_with_subtasks_cannot_be_completed(qapp):
    card = TaskCard({
        "id": 1,
        "title": "Родительская задача",
        "status": "todo",
        "has_subtasks": True,
    })

    assert not card.checkbox.isEnabled()
    done_index = card.editor.status.findData("done")
    assert not card.editor.status.model().item(done_index).isEnabled()


def test_tasks_page_excludes_subtasks_and_marks_their_parent(qapp):
    parent = Task(id=1, project_id=1, title="Родительская задача")
    child = Task(
        id=2,
        project_id=1,
        title="Подзадача",
        parent_task_id=1,
    )

    class FakeTaskService:
        def list(self):
            return [parent, child]

    class FakeProjectService:
        def list(self):
            return [Project(id=1, name="Проект")]

    page = TasksPage(api=_api())
    page.task_service = FakeTaskService()
    page.project_service = FakeProjectService()
    data = page._load()

    assert [task["id"] for task in data["views"]] == [1]
    assert data["views"][0]["has_subtasks"]


def test_notes_page_filters_project_and_shows_all(qapp):
    page = NotesPage(api=_api())
    project_data = _projects()
    page._set_data({
        "notes": [
            {
                "id": note_id,
                "title": f"Заметка {note_id}",
                "content": "Содержание",
                "preview": "Содержание",
                "project": "Документация" if note_id == 2 else "Task Planner",
                "project_id": 2 if note_id == 2 else 1,
                "task_id": None,
                "task": None,
                "updated": "",
                "is_pinned": False,
            }
            for note_id in range(1, 5)
        ],
        "projects": project_data,
        "tasks": [],
    })
    assert set(page._note_cards) == {1, 2, 3, 4}

    page.project_combo.setCurrentIndex(page.project_combo.findData(2))
    assert set(page._note_cards) == {2}

    page.project_combo.setCurrentIndex(0)
    assert set(page._note_cards) == {1, 2, 3, 4}


def test_calendar_filters_project_and_shows_all(qapp):
    page = CalendarPage(api=_api())
    page._set_data({
        "events": [
            {
                "id": event_id,
                "kind": "event",
                "day": event_id,
                "month": page.month,
                "year": page.year,
                "title": f"Событие {event_id}",
                "time": "",
                "project_id": 2 if event_id == 1 else 1,
            }
            for event_id in range(1, 7)
        ],
        "event_models": {},
        "task_models": {},
        "projects": [Project(id=1, name="Task Planner"), Project(id=2, name="Документация")],
    })

    def visible_events():
        days = calendar.monthrange(page.year, page.month)[1]
        return [
            event
            for day in range(1, days + 1)
            for event in page._month_events(day)
        ]

    assert len(visible_events()) == 6

    page.project_combo.setCurrentIndex(page.project_combo.findData(2))
    assert {event["project_id"] for event in visible_events()} == {2}

    page.project_combo.setCurrentIndex(0)
    assert len(visible_events()) == 6
