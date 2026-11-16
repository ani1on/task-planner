from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
)

from client.api.client import ApiClient
from client.api.mapper import task_view
from client.core.constants import STATUS_LABELS, TASK_STATUSES
from client.core.worker import run_async
from client.services.projects import ProjectService
from client.services.tasks import TaskService
from client.ui.components import (
    Badge,
    EmptyState,
    KanbanCard,
    PrimaryButton,
)
from client.ui.error_handler import error_message
from client.ui.mock_data import kanban_columns

from .base_page import BasePage


class KanbanPage(BasePage):
    def __init__(self, api: ApiClient | None = None, demo: bool = False, parent=None):
        super().__init__("Канбан", "Задачи по статусам")

        self.api = api
        self.demo = demo

        self.task_service = TaskService(api) if api else None
        self.project_service = ProjectService(api) if api else None

        self.add_action(PrimaryButton("Новая задача", "plus"))

    # ------------------------------------------------------------------
    # Данные
    # ------------------------------------------------------------------

    def reload(self):
        if self.demo or self.task_service is None:
            self._render(kanban_columns())
            return

        self.show_loading()

        run_async(self._load, self._render, self._show_error)

    def _load(self) -> list[dict]:
        tasks_data = self.task_service.list()
        projects = self.project_service.list() if self.project_service else []

        project_names = {project.id: project.name for project in projects}
        views = [task_view(task, project_names) for task in tasks_data]

        return [
            {
                "key": status,
                "title": STATUS_LABELS.get(status, status),
                "tasks": [task for task in views if task["status"] == status],
            }
            for status in TASK_STATUSES
        ]

    def _show_error(self, error: Exception):
        self.show_error(error_message(error), self.reload)

    # ------------------------------------------------------------------
    # Отрисовка
    # ------------------------------------------------------------------

    def _render(self, columns: list[dict]):
        self.clear_content()

        board = QHBoxLayout()
        board.setSpacing(16)

        for column in columns:
            board.addWidget(self._build_column(column), 1)

        self.content_layout.addLayout(board, 1)
        self.content_layout.addStretch()

    def _build_column(self, column: dict) -> QFrame:
        frame = QFrame()
        frame.setObjectName("KanbanColumn")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        header = QHBoxLayout()
        header.setSpacing(8)

        title = QLabel(column["title"])
        title.setProperty("role", "task-title")

        header.addWidget(title)
        header.addStretch()
        header.addWidget(Badge(str(len(column["tasks"])), "neutral"))

        layout.addLayout(header)

        if not column["tasks"]:
            layout.addWidget(EmptyState("Пусто"))
        else:
            for task in column["tasks"]:
                layout.addWidget(KanbanCard(task))

        layout.addStretch()

        return frame
