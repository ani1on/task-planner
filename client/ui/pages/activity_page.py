from PySide6.QtWidgets import QComboBox, QFrame, QLabel, QVBoxLayout

from client.api.client import ApiClient
from client.api.mapper import format_relative
from client.api.models import Activity
from client.core.worker import run_async
from client.services.activity import ActivityService
from client.services.projects import ProjectService
from client.ui.components import EmptyState, SecondaryButton
from client.ui.error_handler import error_message

from .base_page import BasePage

PAGE_SIZE = 50


class ActivityPage(BasePage):
    """История действий с фильтром по проекту и постраничной загрузкой."""

    def __init__(
        self,
        api: ApiClient,
        parent=None,
    ):
        super().__init__("Активность", "История изменений задач и проектов")
        self.api = api
        self.activity_service = ActivityService(api)
        self.project_service = ProjectService(api)
        self._offset = 0
        self._entries: list[Activity] = []
        self._has_more = False

        self.project_combo = QComboBox()
        self.project_combo.addItem("Все проекты", None)
        self.project_combo.currentIndexChanged.connect(self.reload)
        self.add_action(self.project_combo)

        self.more_button = SecondaryButton("Показать ещё")
        self.more_button.clicked.connect(self._load_more)
        self.more_button.hide()
        self.add_action(self.more_button)

    def reload(self):
        self._offset = 0
        self._entries = []
        self._has_more = False
        self.show_loading()
        run_async(
            self._load_first_page,
            self._show_first_page,
            self._show_error,
            self.project_combo.currentData(),
        )

    def _load_first_page(self, project_id: int | None) -> dict:
        projects = self.project_service.list()
        entries = self.activity_service.list(
            project_id=project_id,
            limit=PAGE_SIZE,
            offset=0,
        )
        return {"projects": projects, "entries": entries}

    def _show_first_page(self, data: dict):
        self._set_projects(data["projects"])
        self._entries = data["entries"]
        self._offset = len(self._entries)
        self._has_more = len(self._entries) == PAGE_SIZE
        self._render(self._entries)

    def _load_more(self):
        self.more_button.setEnabled(False)
        run_async(
            self.activity_service.list,
            self._append_page,
            self._show_error,
            self.project_combo.currentData(),
            None,
            PAGE_SIZE,
            self._offset,
        )

    def _append_page(self, entries: list[Activity]):
        self._has_more = len(entries) == PAGE_SIZE
        self._entries.extend(entries)
        self._offset += len(entries)
        self._render(self._entries)

    def _set_projects(self, projects: list):
        selected = self.project_combo.currentData()
        self.project_combo.blockSignals(True)
        self.project_combo.clear()
        self.project_combo.addItem("Все проекты", None)
        for project in projects:
            self.project_combo.addItem(project.name, project.id)
        index = self.project_combo.findData(selected)
        self.project_combo.setCurrentIndex(max(index, 0))
        self.project_combo.setEnabled(bool(projects))
        self.project_combo.blockSignals(False)

    def _render(self, entries: list[Activity]):
        self.more_button.hide()
        self.clear_content()
        if not entries:
            self.content_layout.addWidget(EmptyState("Записей активности пока нет"))
            return

        for entry in entries:
            card = QFrame()
            card.setProperty("component", "card")
            layout = QVBoxLayout(card)
            layout.setContentsMargins(14, 12, 14, 12)
            layout.setSpacing(4)

            action = QLabel(self._action_label(entry))
            action.setProperty("role", "task-title")
            details = QLabel(
                f"{entry.entity_type} #{entry.entity_id}"
                + (f" · Проект #{entry.project_id}" if entry.project_id else "")
            )
            details.setProperty("role", "muted")
            moment = QLabel(format_relative(entry.created_at))
            moment.setProperty("role", "muted")

            layout.addWidget(action)
            layout.addWidget(details)
            layout.addWidget(moment)
            self.content_layout.addWidget(card)

        if self._has_more:
            self.more_button.setEnabled(True)
            self.more_button.show()

    @staticmethod
    def _action_label(entry: Activity) -> str:
        return entry.action.replace("_", " ").capitalize()

    def _show_error(self, error: Exception):
        self.more_button.setEnabled(True)
        self.more_button.hide()
        self.show_error(error_message(error), self.reload)
