import contextlib

from PySide6.QtWidgets import QGridLayout

from client.api.client import ApiClient
from client.api.mapper import note_view
from client.core.worker import run_async
from client.services.notes import NoteService
from client.services.projects import ProjectService
from client.ui.components import EmptyState, NoteCard, PrimaryButton
from client.ui.error_handler import error_message
from client.ui.mock_data import notes

from .base_page import BasePage

COLUMNS = 3


class NotesPage(BasePage):
    def __init__(self, api: ApiClient | None = None, demo: bool = False, parent=None):
        super().__init__("Заметки", "Идеи, планы и рабочая информация")

        self.api = api
        self.demo = demo
        self.note_service = NoteService(api) if api else None
        self.project_service = ProjectService(api) if api else None

        self.add_action(PrimaryButton("Новая заметка", "plus"))

    # ------------------------------------------------------------------
    # Данные
    # ------------------------------------------------------------------

    def reload(self):
        if self.demo or self.note_service is None:
            self._render(notes())
            return

        self.show_loading()

        run_async(self._load, self._render, self._show_error)

    def _load(self) -> list[dict]:
        notes_data = self.note_service.list()

        projects = []
        if self.project_service:
            with contextlib.suppress(Exception):
                projects = self.project_service.list()

        project_names = {p.id: p.name for p in projects}

        # Сортируем: закреплённые в начале, затем по дате обновления.
        sorted_notes = sorted(
            notes_data,
            key=lambda n: (not n.is_pinned, -(n.updated_at or n.created_at or n.id)),
        )

        return [note_view(note, project_names) for note in sorted_notes]

    def _show_error(self, error: Exception):
        self.show_error(error_message(error), self.reload)

    # ------------------------------------------------------------------
    # Отрисовка
    # ------------------------------------------------------------------

    def _render(self, notes_data: list[dict]):
        self.clear_content()

        if not notes_data:
            self.content_layout.addWidget(EmptyState("Заметок пока нет"))
            self.content_layout.addStretch()
            return

        grid = QGridLayout()
        grid.setSpacing(16)

        for index, note in enumerate(notes_data):
            row, column = divmod(index, COLUMNS)
            grid.addWidget(NoteCard(note), row, column)

        for column in range(COLUMNS):
            grid.setColumnStretch(column, 1)

        self.content_layout.addLayout(grid)
        self.content_layout.addStretch()
