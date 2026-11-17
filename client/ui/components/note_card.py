from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QToolButton,
    QVBoxLayout,
)

from .badge import Badge


class NoteCard(QFrame):
    """Карточка заметки с раскрываемым встроенным редактором."""

    activated = Signal(int)
    save_requested = Signal(int, dict)
    pin_requested = Signal(int, bool)
    delete_requested = Signal(int)

    def __init__(
        self,
        note: dict,
        projects: list | None = None,
        tasks: list | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self.note = note
        self.setProperty("component", "card")
        self.setProperty("clickable", "true")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(8)

        header = QHBoxLayout()
        self.title_label = QLabel(note.get("title", ""))
        self.title_label.setProperty("role", "card-title")
        header.addWidget(self.title_label, 1)
        self.more_button = QToolButton()
        self.more_button.setText("⋯")
        self.more_button.setToolTip("Изменить заметку")
        self.more_button.setProperty("icon", "true")
        self.more_button.clicked.connect(self.toggle_editor)
        header.addWidget(self.more_button)

        self.preview_label = QLabel(note.get("preview", ""))
        self.preview_label.setProperty("role", "muted")
        self.preview_label.setWordWrap(True)

        footer = QHBoxLayout()
        footer.setSpacing(6)
        self.pin_badge = Badge("Закреплена", "primary")
        self.pin_badge.setVisible(bool(note.get("is_pinned")))
        footer.addWidget(self.pin_badge)
        project = note.get("project")
        if project:
            footer.addWidget(Badge(project, "neutral"))
        task = note.get("task")
        if task:
            footer.addWidget(Badge(task, "neutral"))
        footer.addStretch()
        self.updated_label = QLabel(note.get("updated", ""))
        self.updated_label.setProperty("role", "muted")
        footer.addWidget(self.updated_label)

        layout.addLayout(header)
        layout.addWidget(self.preview_label)
        layout.addStretch()
        layout.addLayout(footer)

        self.editor = QFrame()
        self.editor.setProperty("component", "card")
        editor_layout = QVBoxLayout(self.editor)
        editor_layout.setContentsMargins(12, 12, 12, 12)
        editor_layout.setSpacing(8)

        self.title_input = QLineEdit(note.get("title", ""))
        self.error_label = QLabel()
        self.error_label.setProperty("role", "form-error")
        self.error_label.hide()
        self.content_input = QPlainTextEdit(note.get("content") or "")
        self.content_input.setPlaceholderText("Текст заметки")
        self.content_input.setFixedHeight(120)
        self.project_combo = QComboBox()
        self.project_combo.addItem("Без проекта", None)
        for project_item in projects or []:
            self.project_combo.addItem(
                self._value(project_item, "name", "Без названия"),
                self._value(project_item, "id"),
            )
        self._select(self.project_combo, note.get("project_id"))

        self.task_combo = QComboBox()
        self._tasks = tasks or []
        self.project_combo.currentIndexChanged.connect(self._populate_tasks)
        self._populate_tasks()
        self._select(self.task_combo, note.get("task_id"))

        associations = QHBoxLayout()
        associations.addWidget(self.project_combo)
        associations.addWidget(self.task_combo)
        actions = QHBoxLayout()
        pin = QPushButton("Открепить" if note.get("is_pinned") else "Закрепить")
        pin.clicked.connect(
            lambda: self.pin_requested.emit(
                self._note_id(), not self.note.get("is_pinned", False)
            )
        )
        delete = QPushButton("Удалить")
        delete.clicked.connect(lambda: self.delete_requested.emit(self._note_id()))
        save = QPushButton("Сохранить")
        save.clicked.connect(self.save)
        actions.addWidget(pin)
        actions.addStretch()
        actions.addWidget(delete)
        actions.addWidget(save)

        editor_layout.addWidget(QLabel("Название"))
        editor_layout.addWidget(self.title_input)
        editor_layout.addWidget(self.error_label)
        editor_layout.addWidget(QLabel("Содержание"))
        editor_layout.addWidget(self.content_input)
        editor_layout.addLayout(associations)
        editor_layout.addLayout(actions)
        self.editor.hide()
        layout.addWidget(self.editor)

    @staticmethod
    def _value(item, key: str, default=None):
        if isinstance(item, dict):
            return item.get(key, default)
        return getattr(item, key, default)

    @staticmethod
    def _select(combo: QComboBox, value):
        index = combo.findData(value)
        if index >= 0:
            combo.setCurrentIndex(index)

    def _populate_tasks(self, _index: int = -1):
        selected_task_id = self.task_combo.currentData()
        project_id = self.project_combo.currentData()
        self.task_combo.blockSignals(True)
        self.task_combo.clear()
        self.task_combo.addItem("Без задачи", None)
        for task in self._tasks:
            task_project_id = self._value(task, "project_id")
            if task_project_id == project_id:
                self.task_combo.addItem(
                    self._value(task, "title", "Без названия"),
                    self._value(task, "id"),
                )
        self._select(self.task_combo, selected_task_id)
        self.task_combo.blockSignals(False)

    def toggle_editor(self):
        self.editor.setVisible(self.editor.isHidden())

    def save(self):
        title = self.title_input.text().strip()
        if not title:
            self.error_label.setText("Введите название заметки")
            self.error_label.show()
            self.title_input.setFocus()
            return
        self.error_label.hide()
        self.save_requested.emit(
            self._note_id(),
            {
                "title": title,
                "content": self.content_input.toPlainText().strip(),
                "project_id": self.project_combo.currentData(),
                "task_id": self.task_combo.currentData(),
            },
        )

    def _note_id(self) -> int:
        return int(self.note.get("id") or 0)

    def mouseDoubleClickEvent(self, event):
        self.activated.emit(self._note_id())
        super().mouseDoubleClickEvent(event)
