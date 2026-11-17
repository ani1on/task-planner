from PySide6.QtWidgets import QGridLayout, QLineEdit

from client.api.client import ApiClient
from client.api.mapper import project_view
from client.api.models import Project
from client.core.worker import run_async
from client.services.projects import ProjectService
from client.ui.components import EmptyState, PrimaryButton, ProjectCard
from client.ui.crud_actions import ProjectActionsMixin
from client.ui.dialogs.project_members import ProjectMembersPanel
from client.ui.error_handler import error_message
from client.ui.icons import make_icon

from .base_page import BasePage

COLUMNS = 2


class ProjectsPage(ProjectActionsMixin, BasePage):
    def __init__(
        self,
        api: ApiClient,
        user_id: int | None = None,
        parent=None,
    ):
        super().__init__("Проекты", "Проекты, в которых вы участвуете")

        self.api = api
        self.user_id = user_id
        self.project_service = ProjectService(api)

        self._project_models: dict[int, Project] = {}
        self._project_cards: dict[int, ProjectCard] = {}
        self._project_views: list[dict] = []
        self._pending_project_id: int | None = None
        self._projects_loaded = False

        self.search_input = QLineEdit()
        self.search_input.setObjectName("SearchInput")
        self.search_input.setPlaceholderText("Поиск проектов")
        self.search_input.setFixedWidth(220)
        self.search_input.addAction(
            make_icon("search"),
            QLineEdit.ActionPosition.LeadingPosition,
        )
        self.search_input.textChanged.connect(
            lambda _text: self._render_filtered()
        )
        self.add_action(self.search_input)

        create_button = PrimaryButton("Новый проект", "plus")
        create_button.clicked.connect(lambda: self.open_project_dialog())
        self.add_action(create_button)

    # ------------------------------------------------------------------
    # Данные
    # ------------------------------------------------------------------

    def reload(self):
        self._projects_loaded = False

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
        self._projects_loaded = True
        self._project_models = data["models"]
        self._project_views = data["views"]
        self._render_filtered()

    def _render_filtered(self):
        self.clear_content()
        self._project_cards = {}
        query = self.search_input.text().strip().casefold()
        visible_projects = [
            project
            for project in self._project_views
            if not query
            or query in " ".join(
                [
                    str(project.get("name") or ""),
                    str(project.get("description") or ""),
                    " ".join(str(member) for member in project.get("members", [])),
                ]
            ).casefold()
        ]

        if not visible_projects:
            message = (
                "Проектов по запросу не найдено"
                if query
                else "Проектов пока нет"
            )
            self.content_layout.addWidget(EmptyState(message))
            self.content_layout.addStretch()
            self._focus_project()
            return

        grid = QGridLayout()
        grid.setSpacing(16)

        for index, project in enumerate(visible_projects):
            row, column = divmod(index, COLUMNS)

            card = ProjectCard(project)
            self._project_cards[int(project["id"])] = card

            card.delete_requested.connect(self.delete_project)
            card.members_requested.connect(self.manage_members)
            card.save_requested.connect(self.save_project)

            grid.addWidget(card, row, column)

        for column in range(COLUMNS):
            grid.setColumnStretch(column, 1)

        self.content_layout.addLayout(grid)
        self.content_layout.addStretch()
        self._focus_project()

    # ------------------------------------------------------------------
    # Навигация к конкретному проекту
    # ------------------------------------------------------------------

    def show_project(self, project_id: int):
        """Прокручивает к нужному проекту."""
        self._pending_project_id = project_id
        self._focus_project()

    def manage_members(self, project_id: int):
        card = self._project_cards.get(project_id)
        project = self._project_models.get(project_id)
        if card is None or project is None:
            return
        if card.members_panel is not None:
            if card.details.isHidden():
                card.details.show()
                card.members_panel.show()
            else:
                card.members_panel.setVisible(card.members_panel.isHidden())
            return
        card.set_members_panel(
            ProjectMembersPanel(project, self.project_service, card.details)
        )

    def save_project(self, project_id: int, fields: dict):
        project = self._project_models.get(project_id)
        card = self._project_cards.get(project_id)
        if card is None:
            return
        if project is None:
            card.update_project(fields)
            return
        run_async(
            self.project_service.update,
            self._project_saved,
            self._show_error,
            project_id,
            **fields,
        )

    def _project_saved(self, project: Project):
        card = self._project_cards.get(project.id)
        if card is not None:
            card.update_project({
                "name": project.name,
                "description": project.description,
                "color": project.color,
                "status": project.status,
            })
        self._project_models[project.id] = project

    def _focus_project(self):
        if self._pending_project_id is None or not self._projects_loaded:
            return

        card = self._project_cards.get(self._pending_project_id)
        self._pending_project_id = None

        if card is not None:
            self.scroll_to_widget(card)
