import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication

from client.api.client import ApiClient
from client.ui.components.task_card import KanbanCard
from client.ui.pages.kanban_page import KanbanPage


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


def _page_data():
    tasks = [
        {"id": 1, "title": "Задача 1", "project_id": 1, "status": "todo"},
        {"id": 2, "title": "Задача 2", "project_id": 1, "status": "in_progress"},
        {"id": 3, "title": "Задача 3", "project_id": 1, "status": "review"},
        {"id": 4, "title": "Задача 4", "project_id": 2, "status": "todo"},
        {"id": 5, "title": "Задача 5", "project_id": 3, "status": "todo"},
    ]
    for task in tasks:
        task.update({
            "description": "",
            "priority": "medium",
            "due": "",
            "tags": [],
            "has_subtasks": False,
        })
    return {
        "projects": [
            {"id": 1, "name": "Проект 1"},
            {"id": 2, "name": "Проект 2"},
            {"id": 3, "name": "Проект 3"},
        ],
        "tasks": tasks,
        "models": {},
    }


def test_kanban_shows_only_tasks_for_selected_project(qapp):
    page = KanbanPage(api=ApiClient("http://127.0.0.1:1"))
    page._set_data(_page_data())

    assert page.project_combo.currentData() is None
    assert {task["id"] for task in page.visible_tasks} == {1, 2, 3, 4, 5}

    page.project_combo.setCurrentIndex(page.project_combo.findData(1))
    assert {task["project_id"] for task in page.visible_tasks} == {1}
    assert {task["id"] for task in page.visible_tasks} == {1, 2, 3}

    page.project_combo.setCurrentIndex(page.project_combo.findData(2))

    assert {task["project_id"] for task in page.visible_tasks} == {2}
    assert {task["id"] for task in page.visible_tasks} == {4}


def test_kanban_only_allows_changing_task_status(qapp, monkeypatch):
    page = KanbanPage(api=ApiClient("http://127.0.0.1:1"))
    page._set_data(_page_data())
    card = page._task_cards[1]

    monkeypatch.setattr("client.ui.pages.kanban_page.run_async", lambda *args, **kwargs: None)

    assert not hasattr(card, "more_button")
    assert not hasattr(card, "editor")
    assert not hasattr(card, "panel_buttons")
    assert not hasattr(page, "create_button")

    card.status_combo.setCurrentIndex(card.status_combo.findData("done"))

    assert any(
        task["id"] == 1 and task["status"] == "done"
        for task in page.visible_tasks
    )


def test_kanban_parent_with_subtasks_cannot_be_marked_done(qapp):
    card = KanbanCard({
        "id": 1,
        "title": "Родитель",
        "status": "todo",
        "has_subtasks": True,
    })

    done_index = card.status_combo.findData("done")
    assert not card.status_combo.model().item(done_index).isEnabled()
