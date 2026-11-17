from PySide6.QtWidgets import QComboBox, QGridLayout

from client.api.client import ApiClient
from client.api.mapper import note_view
from client.core.worker import run_async
from client.services.notes import NoteService
from client.services.projects import ProjectService
from client.services.tasks import TaskService
from client.ui.components import EmptyState, NoteCard, PrimaryButton
from client.ui.dialogs import ConfirmDialog, NoteDialog
from client.ui.error_handler import error_message

from .base_page import BasePage

COLUMNS = 3


class NotesPage(BasePage):
    def __init__(self, api: ApiClient, parent=None):
        super().__init__("Заметки", "Идеи, планы и рабочая информация")

        self.api = api
        self.note_service = NoteService(api)
        self.project_service = ProjectService(api)
        self.task_service = TaskService(api)
        self._note_cards: dict[int, NoteCard] = {}
        self._all_notes: list[dict] = []
        self._pending_note_id: int | None = None
        self._notes_loaded = False

        self._link_projects = []
        self._link_tasks = []

        self.project_combo = QComboBox()
        self.project_combo.setMinimumWidth(220)
        self.project_combo.setToolTip("Фильтр по проекту")
        self.project_combo.addItem("Все проекты", None)
        self.project_combo.currentIndexChanged.connect(
            lambda _index: self._render(self._all_notes)
        )
        self.add_action(self.project_combo)

        create_button = PrimaryButton("Новая заметка", "plus")
        create_button.clicked.connect(self.open_note_dialog)
        self.add_action(create_button)

    # ------------------------------------------------------------------
    # Данные
    # ------------------------------------------------------------------

    def reload(self):
        self._notes_loaded = False

        self.show_loading()

        run_async(self._load, self._set_data, self._show_error)

    def _load(self) -> dict:
        notes_data = self.note_service.list()
        projects = self.project_service.list()
        tasks = self.task_service.list()

        project_names = {p.id: p.name for p in projects}
        task_names = {task.id: task.title for task in tasks}

        # Закреплённые заметки идут первыми, затем более свежие.
        sorted_notes = sorted(
            notes_data,
            key=lambda note: (
                note.is_pinned,
                (note.updated_at or note.created_at).timestamp()
                if note.updated_at or note.created_at
                else 0,
            ),
            reverse=True,
        )

        views = []
        for note in sorted_notes:
            view = note_view(note, project_names)
            view["content"] = note.content
            view["project_id"] = note.project_id
            view["task_id"] = note.task_id
            view["task"] = task_names.get(note.task_id)
            views.append(view)
        return {"notes": views, "projects": projects, "tasks": tasks}

    def _set_data(self, data: dict):
        self._link_projects = data["projects"]
        self._link_tasks = data["tasks"]
        selected_project_id = self.project_combo.currentData()
        self.project_combo.blockSignals(True)
        self.project_combo.clear()
        self.project_combo.addItem("Все проекты", None)
        for project in self._link_projects:
            project_id = self._item_value(project, "id")
            project_name = self._item_value(project, "name", "Без названия")
            self.project_combo.addItem(project_name, project_id)
        index = self.project_combo.findData(selected_project_id)
        self.project_combo.setCurrentIndex(max(index, 0))
        self.project_combo.blockSignals(False)
        self._render(data["notes"])

    def _show_error(self, error: Exception):
        self.show_error(error_message(error), self.reload)

    # ------------------------------------------------------------------
    # Отрисовка
    # ------------------------------------------------------------------

    def _render(self, notes_data: list[dict]):
        self._notes_loaded = True
        self._all_notes = notes_data
        self._note_cards = {}
        self.clear_content()
        project_id = self.project_combo.currentData()
        notes_data = [
            note for note in notes_data
            if project_id is None or note.get("project_id") == project_id
        ]
        notes_data = sorted(
            notes_data,
            key=lambda note: bool(note.get("is_pinned")),
            reverse=True,
        )

        if not notes_data:
            message = (
                "В выбранном проекте заметок нет"
                if project_id is not None
                else "Заметок пока нет"
            )
            self.content_layout.addWidget(EmptyState(message))
            self.content_layout.addStretch()
            self._focus_note()
            return

        grid = QGridLayout()
        grid.setSpacing(16)

        for index, note in enumerate(notes_data):
            row, column = divmod(index, COLUMNS)
            card = NoteCard(note, self._link_projects, self._link_tasks)
            self._note_cards[int(note["id"])] = card
            card.activated.connect(
                lambda _note_id, card=card: card.toggle_editor()
            )
            card.save_requested.connect(self.save_note_inline)
            card.pin_requested.connect(self.set_note_pinned)
            card.delete_requested.connect(self.delete_note)
            grid.addWidget(card, row, column)

        for column in range(COLUMNS):
            grid.setColumnStretch(column, 1)

        self.content_layout.addLayout(grid)
        self.content_layout.addStretch()
        self._focus_note()

    # ------------------------------------------------------------------
    # Создание и изменение заметок
    # ------------------------------------------------------------------

    def open_note_dialog(self):
        self._show_note_dialog()

    def edit_note(self, note_id: int):
        card = self._note_cards.get(note_id)
        if card is not None:
            card.toggle_editor()

    def save_note_inline(self, note_id: int, payload: dict):
        card = self._note_cards.get(note_id)
        if card is None:
            return
        run_async(
            self.note_service.update,
            self._after_change,
            self._show_error,
            note_id,
            **payload,
        )

    def _show_note_dialog(self):
        dialog = NoteDialog(
            None,
            self._link_projects,
            self._link_tasks,
            self,
        )
        index = dialog.project_combo.findData(self.project_combo.currentData())
        dialog.project_combo.setCurrentIndex(max(index, 0))

        if dialog.exec() != NoteDialog.DialogCode.Accepted:
            return

        payload = dialog.payload()
        run_async(
            self.note_service.create,
            self._after_change,
            self._show_error,
            payload["title"],
            payload["content"],
            payload["project_id"],
            payload["task_id"],
            payload["is_pinned"],
        )

    @staticmethod
    def _item_value(item, key: str, default=None):
        if isinstance(item, dict):
            return item.get(key, default)
        return getattr(item, key, default)

    def set_note_pinned(self, note_id: int, is_pinned: bool):
        card = self._note_cards.get(note_id)
        if card is None:
            return

        run_async(
            self.note_service.update,
            self._after_change,
            self._show_error,
            note_id,
            is_pinned=is_pinned,
        )

    def delete_note(self, note_id: int):
        if note_id not in self._note_cards:
            return

        dialog = ConfirmDialog("Удалить заметку без возможности восстановления?", self)
        if dialog.exec() != ConfirmDialog.DialogCode.Accepted:
            return

        run_async(
            self.note_service.delete,
            self._after_change,
            self._show_error,
            note_id,
        )

    def _after_change(self, _result):
        self.reload()

    # ------------------------------------------------------------------
    # Навигация к конкретной заметке
    # ------------------------------------------------------------------

    def show_note(self, note_id: int):
        """Прокручивает к нужной заметке."""
        self._pending_note_id = note_id
        note = next(
            (item for item in self._all_notes if int(item["id"]) == note_id),
            None,
        )
        project_id = note.get("project_id") if note else None
        index = self.project_combo.findData(project_id)
        self.project_combo.setCurrentIndex(max(index, 0))
        self._focus_note()

    def _focus_note(self):
        if self._pending_note_id is None or not self._notes_loaded:
            return

        card = self._note_cards.get(self._pending_note_id)
        self._pending_note_id = None

        if card is not None:
            self.scroll_to_widget(card)
