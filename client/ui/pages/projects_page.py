from PySide6.QtWidgets import QGridLayout

from client.api.client import ApiClient
from client.api.mapper import project_view
from client.core.worker import run_async
from client.services.projects import ProjectService
from client.ui.components import EmptyState, PrimaryButton, ProjectCard
from client.ui.error_handler import error_message
from client.ui.mock_data import projects

from .base_page import BasePage

COLUMNS = 2


class ProjectsPage(BasePage):
    def __init__(self, api: ApiClient | None = None, demo: bool = False, parent=None):
        super().__init__("Проекты", "Проекты, в которых вы участвуете")

        self.api = api
        self.demo = demo
        self.project_service = ProjectService(api) if api else None

        self.add_action(PrimaryButton("Новый проект", "plus"))

    # ------------------------------------------------------------------
    # Данные
    # ------------------------------------------------------------------

    def reload(self):
        if self.demo or self.project_service is None:
            self._render(projects())
            return

        self.show_loading()

        run_async(self._load, self._render, self._show_error)

    def _load(self) -> list[dict]:
        return [
            project_view(project, members)
            for project, members in self.project_service.list_with_members()
        ]

    def _show_error(self, error: Exception):
        self.show_error(error_message(error), self.reload)

    # ------------------------------------------------------------------
    # Отрисовка
    # ------------------------------------------------------------------

    def _render(self, projects_data: list[dict]):
        self.clear_content()

        if not projects_data:
            self.content_layout.addWidget(EmptyState("Проектов пока нет"))
            self.content_layout.addStretch()
            return

        grid = QGridLayout()
        grid.setSpacing(16)

        for index, project in enumerate(projects_data):
            row, column = divmod(index, COLUMNS)
            grid.addWidget(ProjectCard(project), row, column)

        for column in range(COLUMNS):
            grid.setColumnStretch(column, 1)

        self.content_layout.addLayout(grid)
        self.content_layout.addStretch()
