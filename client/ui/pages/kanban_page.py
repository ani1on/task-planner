from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
)

from client.api.client import ApiClient
from client.api.mapper import task_view
from client.api.models import Task
from client.core.constants import STATUS_DONE, STATUS_LABELS, TASK_STATUSES
from client.core.worker import run_async
from client.services.projects import ProjectService
from client.services.tasks import TaskService
from client.ui.components import (
    Badge,
    EmptyState,
    KanbanCard,
)
from client.ui.error_handler import error_message, handle_api_error

from .base_page import BasePage


class KanbanPage(BasePage):
    def __init__(
        self,
        api: ApiClient,
        user_id: int | None = None,
        parent=None,
    ):
        super().__init__("Канбан", "Задачи по статусам")

        self.api = api
        self.user_id = user_id

        self.task_service = TaskService(api)
        self.project_service = ProjectService(api)

        self._task_models: dict[int, Task] = {}
        self._projects: list = []
        self._all_tasks: list[dict] = []
        self.visible_tasks: list[dict] = []
        self._task_cards: dict[int, KanbanCard] = {}

        self.project_combo = QComboBox()
        self.project_combo.setMinimumWidth(220)
        self.project_combo.currentIndexChanged.connect(self._on_project_changed)
        self.add_action(self.project_combo)

    # ------------------------------------------------------------------
    # Данные
    # ------------------------------------------------------------------

    def reload(self):
        self.show_loading()

        run_async(self._load, self._set_data, self._show_error)

    def _load(self) -> dict:
        tasks_data = self.task_service.list()
        projects = self.project_service.list()

        project_names = {project.id: project.name for project in projects}
        subtask_parent_ids = {
            task.parent_task_id
            for task in tasks_data
            if task.parent_task_id is not None
        }
        views = []
        for task in tasks_data:
            if task.parent_task_id is not None:
                continue
            view = task_view(task, project_names)
            view["project_id"] = task.project_id
            view["has_subtasks"] = task.id in subtask_parent_ids
            views.append(view)

        return {
            "projects": projects,
            "tasks": views,
            "models": {
                task.id: task
                for task in tasks_data
                if task.parent_task_id is None
            },
        }

    def _show_error(self, error: Exception):
        self.show_error(error_message(error), self.reload)

    # ------------------------------------------------------------------
    # Отрисовка
    # ------------------------------------------------------------------

    def _set_data(self, data: dict):
        self._projects = data["projects"]
        self._all_tasks = data["tasks"]
        self._task_models = data["models"]

        selected_project_id = self.project_combo.currentData()
        self.project_combo.blockSignals(True)
        self.project_combo.clear()
        self.project_combo.addItem("Все проекты", None)

        for project in self._projects:
            self.project_combo.addItem(
                self._project_value(project, "name", "Без названия"),
                self._project_value(project, "id"),
            )

        if self._projects:
            index = self.project_combo.findData(selected_project_id)
            self.project_combo.setCurrentIndex(max(index, 0))
            self.project_combo.setEnabled(True)
        else:
            self.project_combo.setEnabled(False)

        self.project_combo.blockSignals(False)
        self._render()

    @staticmethod
    def _project_value(project, key: str, default=None):
        if isinstance(project, dict):
            return project.get(key, default)
        return getattr(project, key, default)

    def _on_project_changed(self, _index: int):
        self._render()

    def _render(self):
        self.clear_content()
        self._task_cards = {}

        project_id = self.project_combo.currentData()
        self.visible_tasks = [
            task
            for task in self._all_tasks
            if project_id is None or task.get("project_id") == project_id
        ]
        columns = [
            {
                "key": status,
                "title": STATUS_LABELS.get(status, status),
                "tasks": [
                    task for task in self.visible_tasks if task["status"] == status
                ],
            }
            for status in TASK_STATUSES
        ]

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
                card = KanbanCard(task)
                self._task_cards[int(task["id"])] = card

                card.status_changed.connect(self._change_task_status)

                layout.addWidget(card)

        layout.addStretch()

        return frame

    def _change_task_status(
        self,
        task_id: int,
        status: str,
        old_status: str,
    ):
        card = self._task_cards.get(task_id)
        if card is None:
            return

        if status == STATUS_DONE and card.task.get("has_subtasks"):
            card.set_status(old_status)
            return

        card.set_status_enabled(False)
        run_async(
            self.task_service.update,
            self._status_saved,
            lambda error: self._status_update_failed(
                task_id,
                old_status,
                error,
            ),
            task_id,
            status=status,
        )

    def _status_saved(self, _task: Task):
        self.reload()

    def _status_update_failed(
        self,
        task_id: int,
        old_status: str,
        error: Exception,
    ):
        card = self._task_cards.get(task_id)
        if card is not None:
            card.set_status(old_status)
            card.set_status_enabled(True)
        handle_api_error(error, self)
