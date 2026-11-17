from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QPlainTextEdit,
)

from client.ui.components import (
    FormField,
    PrimaryButton,
    SecondaryButton,
    TextInput,
)

from .base import BaseDialog


class NoteDialog(BaseDialog):
    """Создание и редактирование заметки."""

    def __init__(
        self,
        note: dict | None = None,
        projects: list | None = None,
        tasks: list | None = None,
        parent=None,
    ):
        super().__init__(parent)

        self.note = note
        self.projects = projects or []
        self.tasks = tasks or []
        self.setWindowTitle(
            "Новая заметка" if note is None else "Редактирование заметки"
        )
        self.setMinimumWidth(480)

        self.layout.setContentsMargins(24, 22, 24, 20)
        self.layout.setSpacing(14)

        self.title_field = FormField("Название", TextInput("Название заметки"))
        self.content_edit = QPlainTextEdit()
        self.content_edit.setPlaceholderText("Текст заметки")
        self.content_edit.setMinimumHeight(220)
        self.content_field = FormField("Содержание", self.content_edit)

        self.project_combo = QComboBox()
        self.project_combo.addItem("Без проекта", None)
        for project in self.projects:
            self.project_combo.addItem(
                self._value(project, "name", "Без названия"),
                self._value(project, "id"),
            )
        self.project_field = FormField("Проект", self.project_combo)

        self.task_combo = QComboBox()
        self.task_field = FormField("Задача", self.task_combo)

        self.pinned_check = QCheckBox("Закрепить заметку")

        self.layout.addWidget(self.title_field)
        self.layout.addWidget(self.content_field)
        self.layout.addWidget(self.project_field)
        self.layout.addWidget(self.task_field)
        self.layout.addWidget(self.pinned_check)

        buttons = QHBoxLayout()
        buttons.setSpacing(8)

        cancel = SecondaryButton("Отмена")
        cancel.clicked.connect(self.reject)

        save = PrimaryButton("Создать" if note is None else "Сохранить")
        save.setDefault(True)
        save.clicked.connect(self.accept)

        buttons.addStretch()
        buttons.addWidget(cancel)
        buttons.addWidget(save)
        self.layout.addLayout(buttons)

        self.project_combo.currentIndexChanged.connect(self._project_changed)
        self.task_combo.currentIndexChanged.connect(self._task_changed)

        if note is not None:
            self.title_field.field.setText(note.get("title", ""))
            self.content_edit.setPlainText(
                note.get("content", note.get("preview", ""))
            )
            self.pinned_check.setChecked(bool(note.get("is_pinned", False)))

        self._select_project(note.get("project_id") if note else None)
        self._refresh_tasks(note.get("task_id") if note else None)
        self.title_field.field.setFocus()

    @staticmethod
    def _value(item, key: str, default=None):
        if isinstance(item, dict):
            return item.get(key, default)
        return getattr(item, key, default)

    def _select_project(self, project_id: int | None):
        index = self.project_combo.findData(project_id)
        self.project_combo.setCurrentIndex(max(index, 0))

    def _project_changed(self, _index: int):
        self._refresh_tasks()

    def _task_changed(self, _index: int):
        task_id = self.task_combo.currentData()
        if task_id is None:
            return

        task = next(
            (item for item in self.tasks if self._value(item, "id") == task_id),
            None,
        )
        if task is None:
            return

        project_id = self._value(task, "project_id")
        if self.project_combo.currentData() != project_id:
            self._select_project(project_id)
            self._refresh_tasks(task_id)

    def _refresh_tasks(self, selected_task_id: int | None = None):
        project_id = self.project_combo.currentData()
        self.task_combo.blockSignals(True)
        self.task_combo.clear()
        self.task_combo.addItem("Без задачи", None)

        for task in self.tasks:
            task_project_id = self._value(task, "project_id")
            if project_id is not None and task_project_id != project_id:
                continue
            self.task_combo.addItem(
                self._value(task, "title", "Без названия"),
                self._value(task, "id"),
            )

        task_index = self.task_combo.findData(selected_task_id)
        self.task_combo.setCurrentIndex(max(task_index, 0))
        self.task_combo.blockSignals(False)

    def accept(self):
        if not self.title_field.value().strip():
            self.title_field.set_error("Введите название заметки")
            return

        if not self.content_edit.toPlainText().strip():
            self.content_field.set_error("Введите текст заметки")
            return

        super().accept()

    def payload(self) -> dict:
        return {
            "title": self.title_field.value().strip(),
            "content": self.content_edit.toPlainText().strip(),
            "project_id": self.project_combo.currentData(),
            "task_id": self.task_combo.currentData(),
            "is_pinned": self.pinned_check.isChecked(),
        }
