from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
)

from client.api.client import ApiClient
from client.api.mapper import (
    dashboard_stats_view,
    project_view,
    task_view,
)
from client.api.models import Dashboard, Task
from client.core.constants import PROJECT_COLORS
from client.core.worker import run_async
from client.services.dashboard import DashboardService
from client.services.tasks import TaskService
from client.ui.components import (
    EmptyState,
    ProgressBar,
    SectionTitle,
    StatCard,
    TaskCard,
)
from client.ui.crud_actions import TaskActionsMixin
from client.ui.error_handler import error_message

from .base_page import BasePage


class ProjectProgressRow(QFrame):
    """Компактная строка прогресса проекта для дашборда."""

    def __init__(self, project: dict, parent=None):
        super().__init__(parent)

        self.setProperty("component", "card")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        header = QHBoxLayout()
        header.setSpacing(8)

        color = PROJECT_COLORS.get(project.get("color"), PROJECT_COLORS["blue"])
        dot = QFrame()
        dot.setFixedSize(10, 10)
        dot.setStyleSheet(f"background-color: {color}; border-radius: 5px;")

        name = QLabel(project.get("name", ""))
        name.setProperty("role", "task-title")

        done = project.get("done", 0)
        total = project.get("total", 0)
        percent = int(done / total * 100) if total else 0

        value = QLabel(f"{percent}%")
        value.setProperty("role", "muted")

        header.addWidget(dot)
        header.addWidget(name)
        header.addStretch()
        header.addWidget(value)

        progress = ProgressBar(percent)

        layout.addLayout(header)
        layout.addWidget(progress)


class DashboardPage(TaskActionsMixin, BasePage):
    def __init__(
        self,
        api: ApiClient,
        user_id: int | None = None,
        parent=None,
    ):
        super().__init__("Дашборд", "Обзор задач, проектов и активности")

        self.api = api
        self.user_id = user_id
        self.dashboard_service = DashboardService(api)
        self.task_service = TaskService(api)

        self._task_models: dict[int, Task] = {}
        self._task_cards: dict[int, TaskCard] = {}
        self._subtask_parent_ids: set[int] = set()

    # ------------------------------------------------------------------
    # Данные
    # ------------------------------------------------------------------

    def reload(self):
        self.show_loading()

        run_async(
            self._load_dashboard,
            self._render_loaded,
            self._show_error,
        )

    def _load_dashboard(self) -> tuple[Dashboard, set[int]]:
        dashboard = self.dashboard_service.get()
        tasks = self.task_service.list()
        parent_ids = {
            task.parent_task_id
            for task in tasks
            if task.parent_task_id is not None
        }
        return dashboard, parent_ids

    def _render_loaded(self, data: tuple[Dashboard, set[int]]):
        dashboard, self._subtask_parent_ids = data
        self._render(dashboard)

    def _show_error(self, error: Exception):
        self.show_error(error_message(error), self.reload)

    # ------------------------------------------------------------------
    # Отрисовка
    # ------------------------------------------------------------------

    def _render(self, dashboard: Dashboard):
        self._task_models = {
            task.id: task
            for task in dashboard.upcoming_tasks
            if task.parent_task_id is None
        }

        self.clear_content()

        self._build_stats(dashboard_stats_view(dashboard.stats))
        self._build_columns(dashboard)

    def _build_stats(self, stats: list[dict]):
        layout = QHBoxLayout()
        layout.setSpacing(16)

        for stat in stats:
            layout.addWidget(
                StatCard(
                    label=stat["label"],
                    value=stat["value"],
                    accent=stat["accent"],
                ),
                1,
            )

        self.content_layout.addLayout(layout)

    def _build_columns(self, dashboard: Dashboard):
        layout = QHBoxLayout()
        layout.setSpacing(16)

        project_names = {
            project.id: project.name for project in dashboard.projects
        }

        today_tasks = [
            {
                **task_view(task, project_names),
                "has_subtasks": task.id in self._subtask_parent_ids,
            }
            for task in [
                task
                for task in dashboard.upcoming_tasks
                if task.parent_task_id is None
            ][:3]
        ]

        project_rows = [
            project_view(project) for project in dashboard.projects[:3]
        ]

        layout.addLayout(self._build_today(today_tasks), 1)
        layout.addLayout(self._build_project_rows(project_rows), 1)

        self.content_layout.addLayout(layout)
        self.content_layout.addStretch()

    def _build_today(self, tasks: list[dict]) -> QVBoxLayout:
        layout = QVBoxLayout()
        layout.setSpacing(12)
        self._task_cards = {}

        layout.addWidget(SectionTitle("Задачи на сегодня"))

        if not tasks:
            layout.addWidget(EmptyState("На сегодня задач нет"))
        else:
            for task in tasks:
                card = TaskCard(task)
                self._task_cards[int(task["id"])] = card

                card.completion_changed.connect(self.toggle_task)
                card.set_panel_enabled(True)
                card.set_editing_enabled(False)

                layout.addWidget(card)

        layout.addStretch()

        return layout

    def _build_project_rows(self, projects: list[dict]) -> QVBoxLayout:
        layout = QVBoxLayout()
        layout.setSpacing(12)

        layout.addWidget(SectionTitle("Прогресс проектов"))

        if not projects:
            layout.addWidget(EmptyState("Проектов пока нет"))
        else:
            for project in projects:
                layout.addWidget(ProjectProgressRow(project))

        layout.addStretch()

        return layout
