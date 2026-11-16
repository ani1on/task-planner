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
from client.api.models import Dashboard
from client.core.constants import PROJECT_COLORS
from client.core.worker import run_async
from client.services.dashboard import DashboardService
from client.ui.components import (
    EmptyState,
    PrimaryButton,
    ProgressBar,
    SectionTitle,
    StatCard,
    TaskCard,
)
from client.ui.error_handler import error_message
from client.ui.mock_data import (
    dashboard_stats,
    projects,
    tasks,
)

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


class DashboardPage(BasePage):
    def __init__(self, api: ApiClient | None = None, demo: bool = False, parent=None):
        super().__init__("Дашборд", "Обзор задач, проектов и активности")

        self.api = api
        self.demo = demo
        self.dashboard_service = DashboardService(api) if api else None

        create_button = PrimaryButton("Новая задача", "plus")
        self.add_action(create_button)

    # ------------------------------------------------------------------
    # Данные
    # ------------------------------------------------------------------

    def reload(self):
        if self.demo or self.dashboard_service is None:
            self._render_demo()
            return

        self.show_loading()

        run_async(
            self.dashboard_service.get,
            self._render,
            self._show_error,
        )

    def _show_error(self, error: Exception):
        self.show_error(error_message(error), self.reload)

    # ------------------------------------------------------------------
    # Отрисовка
    # ------------------------------------------------------------------

    def _render(self, dashboard: Dashboard):
        self.clear_content()

        self._build_stats(dashboard_stats_view(dashboard.stats))
        self._build_columns(dashboard)

    def _render_demo(self):
        self.clear_content()

        self._build_stats(dashboard_stats())

        layout = QHBoxLayout()
        layout.setSpacing(16)

        layout.addLayout(self._build_today(tasks()[:3]), 1)
        layout.addLayout(self._build_project_rows(projects()[:3]), 1)

        self.content_layout.addLayout(layout)
        self.content_layout.addStretch()

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
            task_view(task, project_names)
            for task in dashboard.upcoming_tasks[:3]
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

        layout.addWidget(SectionTitle("Задачи на сегодня"))

        if not tasks:
            layout.addWidget(EmptyState("На сегодня задач нет"))
        else:
            for task in tasks:
                layout.addWidget(TaskCard(task))

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
