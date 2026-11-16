from datetime import datetime

from PySide6.QtCore import QDate, QDateTime, QTime
from PySide6.QtWidgets import (
    QComboBox,
    QDateTimeEdit,
    QHBoxLayout,
    QPlainTextEdit,
)

from client.api.models import Member, Project, Task
from client.core.constants import (
    PRIORITY_LABELS,
    STATUS_LABELS,
    TASK_PRIORITIES,
    TASK_STATUSES,
)
from client.ui.components import (
    FormField,
    PrimaryButton,
    SecondaryButton,
    TextInput,
)

from .base import BaseDialog

# Минимальная дата означает «значение не задано» (см. setSpecialValueText).
MIN_DATETIME = QDateTime(QDate(2000, 1, 1), QTime(0, 0))


def to_iso(value: QDateTime) -> str | None:
    """Преобразует значение виджета в ISO-строку или None."""
    if value == MIN_DATETIME:
        return None

    moment = value.toPython()

    if moment.tzinfo is None:
        moment = moment.astimezone()

    return moment.isoformat()


def to_widget_datetime(moment: datetime | None) -> QDateTime:
    if moment is None:
        return MIN_DATETIME

    return QDateTime(moment)


class TaskDialog(BaseDialog):
    """Создание и редактирование задачи."""

    def __init__(
        self,
        projects: list[Project] | tuple[Project, ...],
        members_map: dict[int, list[Member]] | None = None,
        task: Task | None = None,
        project_id: int | None = None,
        parent=None,
    ):
        super().__init__(parent)

        self.task = task
        self.projects = list(projects)
        self.members_map = members_map or {}

        self.setWindowTitle(
            "Новая задача" if task is None else "Редактирование задачи"
        )
        self.setMinimumWidth(520)

        self.layout.setContentsMargins(24, 22, 24, 20)
        self.layout.setSpacing(14)

        self._build_fields()
        self._fill(task, project_id)

    # ------------------------------------------------------------------
    # Построение формы
    # ------------------------------------------------------------------

    def _build_fields(self):
        self.title_field = FormField(
            "Название",
            TextInput("Например: Подготовить отчёт"),
        )

        self.project_combo = QComboBox()
        self.project_combo.currentIndexChanged.connect(self._on_project_changed)
        self.project_field = FormField("Проект", self.project_combo)

        self.assignee_combo = QComboBox()
        self.assignee_field = FormField("Исполнитель", self.assignee_combo)

        self.status_combo = QComboBox()
        for status in TASK_STATUSES:
            self.status_combo.addItem(STATUS_LABELS[status], status)

        self.priority_combo = QComboBox()
        for priority in TASK_PRIORITIES:
            self.priority_combo.addItem(PRIORITY_LABELS[priority], priority)

        self.status_field = FormField("Статус", self.status_combo)
        self.priority_field = FormField("Приоритет", self.priority_combo)

        self.start_edit = self._make_datetime_edit()
        self.due_edit = self._make_datetime_edit()

        self.start_field = FormField("Начало", self.start_edit)
        self.due_field = FormField("Дедлайн", self.due_edit)

        self.description_edit = QPlainTextEdit()
        self.description_edit.setPlaceholderText(
            "Детали, критерии готовности, ссылки",
        )
        self.description_edit.setFixedHeight(96)

        self.description_field = FormField("Описание", self.description_edit)

        self.layout.addWidget(self.title_field)
        self.layout.addLayout(self._row(self.project_field, self.assignee_field))
        self.layout.addLayout(self._row(self.status_field, self.priority_field))
        self.layout.addLayout(self._row(self.start_field, self.due_field))
        self.layout.addWidget(self.description_field)

        buttons = QHBoxLayout()
        buttons.setSpacing(8)

        cancel = SecondaryButton("Отмена")
        cancel.clicked.connect(self.reject)

        save = PrimaryButton("Создать" if self.task is None else "Сохранить")
        save.setDefault(True)
        save.clicked.connect(self.accept)

        buttons.addStretch()
        buttons.addWidget(cancel)
        buttons.addWidget(save)

        self.layout.addLayout(buttons)

        self.title_field.field.setFocus()

    @staticmethod
    def _row(*fields: FormField) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(14)

        for field in fields:
            row.addWidget(field, 1)

        return row

    @staticmethod
    def _make_datetime_edit() -> QDateTimeEdit:
        edit = QDateTimeEdit()
        edit.setCalendarPopup(True)
        edit.setDisplayFormat("dd.MM.yyyy HH:mm")
        edit.setMinimumDateTime(MIN_DATETIME)
        edit.setDateTime(MIN_DATETIME)
        edit.setSpecialValueText("Не задано")
        edit.setMinimumWidth(170)

        return edit

    # ------------------------------------------------------------------
    # Заполнение значениями
    # ------------------------------------------------------------------

    def _fill(self, task: Task | None, project_id: int | None):
        if not self.projects:
            self.project_combo.addItem("Сначала создайте проект", None)
            self.project_combo.setEnabled(False)
        else:
            for project in self.projects:
                self.project_combo.addItem(project.name, project.id)

        if task is None:
            self._select_data(self.project_combo, project_id)
            self._rebuild_assignees()
            return

        self.project_combo.setEnabled(False)
        self.project_combo.setToolTip("Проект задачи нельзя изменить")

        self._select_data(self.project_combo, task.project_id)

        self.title_field.field.setText(task.title or "")
        self.description_edit.setPlainText(task.description or "")
        self._select_data(self.status_combo, task.status)
        self._select_data(self.priority_combo, task.priority)

        self.start_edit.setDateTime(to_widget_datetime(task.start_at))
        self.due_edit.setDateTime(to_widget_datetime(task.due_at))

        self._rebuild_assignees()
        self._select_data(self.assignee_combo, task.assignee_id)

    def _on_project_changed(self, _index: int):
        self._rebuild_assignees()

    def _rebuild_assignees(self):
        self.assignee_combo.blockSignals(True)
        self.assignee_combo.clear()
        self.assignee_combo.addItem("Не назначен", None)

        project_id = self.project_combo.currentData()

        for member in self.members_map.get(project_id, []):
            self.assignee_combo.addItem(member.nick_name, member.user_id)

        self.assignee_combo.blockSignals(False)

    @staticmethod
    def _select_data(combo: QComboBox, value):
        index = combo.findData(value)

        if index >= 0:
            combo.setCurrentIndex(index)

    # ------------------------------------------------------------------
    # Результат
    # ------------------------------------------------------------------

    def accept(self):
        if not self.title_field.value().strip():
            self.title_field.set_error("Введите название задачи")
            return

        if self.task is None and self.project_combo.currentData() is None:
            self.project_field.set_error("Сначала создайте проект")
            return

        start = self.start_edit.dateTime()
        due = self.due_edit.dateTime()

        if start != MIN_DATETIME and due != MIN_DATETIME and due < start:
            self.due_field.set_error("Дедлайн раньше даты начала")
            return

        super().accept()

    def payload(self) -> dict:
        data = {
            "title": self.title_field.value().strip(),
            "description": self.description_edit.toPlainText().strip() or None,
            "status": self.status_combo.currentData(),
            "priority": self.priority_combo.currentData(),
            "assignee_id": self.assignee_combo.currentData(),
            "start_at": to_iso(self.start_edit.dateTime()),
            "due_at": to_iso(self.due_edit.dateTime()),
        }

        if self.task is None:
            data["project_id"] = self.project_combo.currentData()

        return data
