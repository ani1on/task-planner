from datetime import datetime, timedelta

from PySide6.QtCore import QDateTime, QLocale, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateTimeEdit,
    QHBoxLayout,
    QPlainTextEdit,
)

from client.api.models import Event, Project
from client.services.reminders import ReminderService
from client.ui.components import FormField, PrimaryButton, SecondaryButton, TextInput

from .base import BaseDialog


def _widget_datetime(value: datetime | None, fallback: datetime) -> QDateTime:
    return QDateTime(value or fallback)


def _iso(value: QDateTime) -> str:
    moment = value.toPython()
    if moment.tzinfo is None:
        moment = moment.astimezone()
    return moment.isoformat()


class EventDialog(BaseDialog):
    """Создание и редактирование календарного события."""

    def __init__(
        self,
        projects: list[Project],
        event: Event | None = None,
        start_at: datetime | None = None,
        reminder_service: ReminderService | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self.event = event
        self.delete_requested = False

        self.setWindowTitle("Новое событие" if event is None else "Событие")
        self.setMinimumWidth(520)
        self.layout.setContentsMargins(24, 22, 24, 20)
        self.layout.setSpacing(12)

        self.title_input = TextInput("Название события")
        self.title_field = FormField("Название", self.title_input)
        self.project_combo = QComboBox()
        self.project_combo.addItem("Без проекта", None)
        for project in projects:
            self.project_combo.addItem(project.name, project.id)
        self.project_field = FormField("Проект", self.project_combo)

        initial_start = (
            event.start_at if event is not None
            else start_at or datetime.now().astimezone().replace(
                hour=9, minute=0, second=0, microsecond=0
            )
        )
        initial_end = (
            event.end_at if event is not None
            else initial_start + timedelta(hours=1)
        )
        self.start_edit = self._datetime_edit(initial_start)
        self.end_edit = self._datetime_edit(initial_end)
        self.start_field = FormField("Начало", self.start_edit)
        self.end_field = FormField("Окончание", self.end_edit)

        self.all_day = QCheckBox("Весь день")
        self.location_input = TextInput("Место проведения")
        self.location_field = FormField("Место", self.location_input)
        self.description_input = QPlainTextEdit()
        self.description_input.setPlaceholderText("Описание")
        self.description_input.setFixedHeight(90)
        self.description_field = FormField("Описание", self.description_input)

        self.layout.addWidget(self.title_field)
        self.layout.addWidget(self.project_field)
        dates = QHBoxLayout()
        dates.addWidget(self.start_field)
        dates.addWidget(self.end_field)
        self.layout.addLayout(dates)
        self.layout.addWidget(self.all_day)
        self.layout.addWidget(self.location_field)
        self.layout.addWidget(self.description_field)

        buttons = QHBoxLayout()
        buttons.addStretch()
        if event is not None:
            delete = SecondaryButton("Удалить")
            delete.clicked.connect(self._delete)
            buttons.addWidget(delete)
        cancel = SecondaryButton("Отмена")
        cancel.clicked.connect(self.reject)
        save = PrimaryButton("Создать" if event is None else "Сохранить")
        save.clicked.connect(self.accept)
        buttons.addWidget(cancel)
        buttons.addWidget(save)
        self.layout.addLayout(buttons)

        if event is not None:
            self.title_input.setText(event.title)
            self.project_combo.setCurrentIndex(
                max(self.project_combo.findData(event.project_id), 0)
            )
            self.all_day.setChecked(event.all_day)
            self.location_input.setText(event.location or "")
            self.description_input.setPlainText(event.description or "")

    @staticmethod
    def _datetime_edit(value: datetime) -> QDateTimeEdit:
        editor = QDateTimeEdit(_widget_datetime(value, datetime.now().astimezone()))
        editor.setCalendarPopup(True)
        editor.setDisplayFormat("dd.MM.yyyy HH:mm")
        editor.setLocale(QLocale("ru_RU"))
        editor.calendarWidget().setFirstDayOfWeek(Qt.DayOfWeek.Monday)
        return editor

    def _delete(self):
        self.delete_requested = True
        self.done(self.DialogCode.Accepted)

    def accept(self):
        if not self.title_input.text().strip():
            self.title_field.set_error("Введите название события")
            return
        if self.end_edit.dateTime() < self.start_edit.dateTime():
            self.end_field.set_error("Окончание раньше начала")
            return
        super().accept()

    def payload(self) -> dict:
        return {
            "title": self.title_input.text().strip(),
            "project_id": self.project_combo.currentData(),
            "start_at": _iso(self.start_edit.dateTime()),
            "end_at": _iso(self.end_edit.dateTime()),
            "all_day": self.all_day.isChecked(),
            "location": self.location_input.text().strip() or None,
            "description": self.description_input.toPlainText().strip() or None,
        }
