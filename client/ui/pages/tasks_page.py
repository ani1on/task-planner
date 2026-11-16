from datetime import date, datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from client.api.client import ApiClient
from client.api.mapper import task_view
from client.api.models import Task
from client.core.worker import run_async
from client.services.projects import ProjectService
from client.services.tasks import TaskService
from client.ui.components import (
    EmptyState,
    PrimaryButton,
    SecondaryButton,
    TaskCard,
)
from client.ui.crud_actions import TaskActionsMixin
from client.ui.error_handler import error_message
from client.ui.mock_data import tasks

from .base_page import BasePage, clear_layout

FILTERS = [
    ("all", "Все"),
    ("today", "Сегодня"),
    ("active", "Активные"),
    ("overdue", "Просроченные"),
    ("done", "Выполненные"),
]


def matches_filter(task: dict, key: str) -> bool:
    if key == "all":
        return True

    if key == "done":
        return bool(task.get("done"))

    if key == "active":
        return not task.get("done")

    due_at = task.get("due_at")

    if due_at is None:
        return False

    if key == "today":
        return due_at.date() == date.today()  # noqa: DTZ011

    if key == "overdue":
        return not task.get("done") and due_at < datetime.now().astimezone()

    return True


class TasksPage(TaskActionsMixin, BasePage):
    def __init__(self, api: ApiClient | None = None, demo: bool = False, parent=None):
        super().__init__("Задачи", "Все задачи вашей команды")

        self.api = api
        self.demo = demo

        self.task_service = TaskService(api) if api else None
        self.project_service = ProjectService(api) if api else None

        self.all_tasks: list[dict] = []
        self._task_models: dict[int, Task] = {}
        self.active_filter = "all"

        create_button = PrimaryButton("Новая задача", "plus")
        create_button.clicked.connect(lambda: self.open_task_dialog())
        self.add_action(create_button)

        self._build_filters()

        self.tasks_container = QWidget()
        self.tasks_layout = QVBoxLayout(self.tasks_container)
        self.tasks_layout.setContentsMargins(0, 0, 0, 0)
        self.tasks_layout.setSpacing(10)

        self.content_layout.addWidget(self.tasks_container)
        self.content_layout.addStretch()

    def _build_filters(self):
        layout = QHBoxLayout()
        layout.setSpacing(8)

        self.filter_group = QButtonGroup(self)
        self.filter_group.setExclusive(True)
        self.filter_group.idClicked.connect(self._on_filter_changed)

        for index, (key, label) in enumerate(FILTERS):
            chip = QPushButton(label)
            chip.setCheckable(True)
            chip.setCursor(Qt.CursorShape.PointingHandCursor)
            chip.setProperty("chip", "true")
            chip.setChecked(index == 0)

            self.filter_group.addButton(chip, index)
            layout.addWidget(chip)

        layout.addStretch()

        self.content_layout.addLayout(layout)

    # ------------------------------------------------------------------
    # Данные
    # ------------------------------------------------------------------

    def reload(self):
        if self.demo or self.task_service is None:
            self._set_tasks({"views": tasks(), "models": {}})
            return

        clear_layout(self.tasks_layout)
        self.tasks_layout.addWidget(EmptyState("Загрузка..."))

        run_async(self._load, self._set_tasks, self._show_error)

    def _load(self) -> dict:
        tasks_data = self.task_service.list()
        projects = self.project_service.list() if self.project_service else []

        project_names = {project.id: project.name for project in projects}

        return {
            "views": [task_view(task, project_names) for task in tasks_data],
            "models": {task.id: task for task in tasks_data},
        }

    def _show_error(self, error: Exception):
        clear_layout(self.tasks_layout)

        self.tasks_layout.addWidget(EmptyState(error_message(error)))

        retry = SecondaryButton("Повторить")
        retry.clicked.connect(self.reload)
        self.tasks_layout.addWidget(retry, 0, Qt.AlignmentFlag.AlignHCenter)

    # ------------------------------------------------------------------
    # Фильтры и отрисовка
    # ------------------------------------------------------------------

    def _on_filter_changed(self, index: int):
        if 0 <= index < len(FILTERS):
            self.active_filter = FILTERS[index][0]
            self._render_tasks()

    def _set_tasks(self, data: dict):
        self._task_models = data["models"]
        self.all_tasks = data["views"]
        self._render_tasks()

    def _render_tasks(self):
        clear_layout(self.tasks_layout)

        filtered = [
            task
            for task in self.all_tasks
            if matches_filter(task, self.active_filter)
        ]

        if not filtered:
            self.tasks_layout.addWidget(EmptyState("Задач нет"))
            return

        for task in filtered:
            card = TaskCard(task)

            card.activated.connect(self.edit_task)
            card.edit_requested.connect(self.edit_task)
            card.completion_changed.connect(self.toggle_task)
            card.delete_requested.connect(self.delete_task)

            self.tasks_layout.addWidget(card)
