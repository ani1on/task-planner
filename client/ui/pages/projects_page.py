from PySide6.QtWidgets import QGridLayout

from client.api.client import ApiClient
from client.api.mapper import project_view
from client.api.models import Project
from client.core.worker import run_async
from client.services.projects import ProjectService
from client.ui.components import EmptyState, PrimaryButton, ProjectCard
from client.ui.crud_actions import ProjectActionsMixin
from client.ui.error_handler import error_message
from client.ui.mock_data import projects

from .base_page import BasePage

COLUMNS = 2


class ProjectsPage(ProjectActionsMixin, BasePage):
    def __init__(self, api: ApiClient | None = None, demo: bool = False, parent=None):
        super().__init__("Проекты", "Проекты, в которых вы участвуете")

        self.api = api
        self.demo = demo
        self.project_service = ProjectService(api) if api else None

        self._project_models: dict[int, Project] = {}

        create_button = PrimaryButton("Новый проект", "plus")
        create_button.clicked.connect(lambda: self.open_project_dialog())
        self.add_action(create_button)

    # ------------------------------------------------------------------
    # Данные
    # ------------------------------------------------------------------

    def reload(self):
        if self.demo or self.project_service is None:
            self._render({"views": projects(), "models": {}})
            return

        self.show_loading()

        run_async(self._load, self._render, self._show_error)

    def _load(self) -> dict:
        pairs = self.project_service.list_with_members()

        return {
            "views": [
                project_view(project, members) for project, members in pairs
            ],
            "models": {project.id: project for project, _ in pairs},
        }

    def _show_error(self, error: Exception):
        self.show_error(error_message(error), self.reload)

    # ------------------------------------------------------------------
    # Отрисовка
    # ------------------------------------------------------------------

    def _render(self, data: dict):
        self._project_models = data["models"]

        self.clear_content()

        if not data["views"]:
            self.content_layout.addWidget(EmptyState("Проектов пока нет"))
            self.content_layout.addStretch()
            return

        grid = QGridLayout()
        grid.setSpacing(16)

        for index, project in enumerate(data["views"]):
            row, column = divmod(index, COLUMNS)

            card = ProjectCard(project)

            card.activated.connect(self.edit_project)
            card.edit_requested.connect(self.edit_project)
            card.archive_requested.connect(self.archive_project)
            card.delete_requested.connect(self.delete_project)

            grid.addWidget(card, row, column)

        for column in range(COLUMNS):
            grid.setColumnStretch(column, 1)

        self.content_layout.addLayout(grid)
        self.content_layout.addStretch()
