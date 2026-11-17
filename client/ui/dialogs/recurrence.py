from datetime import datetime

from PySide6.QtCore import QDateTime, QLocale, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateTimeEdit,
    QHBoxLayout,
    QLabel,
    QSpinBox,
)

from client.api.models import Recurrence
from client.ui.components import FormField, PrimaryButton, SecondaryButton

from .base import BaseDialog

FREQUENCIES = (
    ("Ежедневно", "daily"),
    ("Еженедельно", "weekly"),
    ("Ежемесячно", "monthly"),
)


def _iso(editor: QDateTimeEdit) -> str:
    value = editor.dateTime().toPython()
    if value.tzinfo is None:
        value = value.astimezone()
    return value.isoformat()


def _editor(value: datetime) -> QDateTimeEdit:
    editor = QDateTimeEdit(QDateTime(value))
    editor.setCalendarPopup(True)
    editor.setDisplayFormat("dd.MM.yyyy HH:mm")
    editor.setLocale(QLocale("ru_RU"))
    editor.calendarWidget().setFirstDayOfWeek(Qt.DayOfWeek.Monday)
    return editor


class RecurrenceDialog(BaseDialog):
    """Параметры повтора задачи в формате серверной схемы."""

    def __init__(self, recurrence: Recurrence | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Повторение задачи")
        self.setMinimumWidth(440)
        self.layout.setContentsMargins(24, 22, 24, 20)
        self.layout.setSpacing(12)

        self.frequency = QComboBox()
        for label, value in FREQUENCIES:
            self.frequency.addItem(label, value)
        self.interval = QSpinBox()
        self.interval.setRange(1, 365)
        self.interval.setValue(1)
        self.day_of_month = QSpinBox()
        self.day_of_month.setRange(1, 31)
        self.day_of_month.setValue(1)
        now = datetime.now().astimezone()
        self.start_at = _editor(recurrence.start_at if recurrence else now)
        self.end_enabled = QCheckBox("Завершить повторение")
        self.end_at = _editor(
            recurrence.end_at if recurrence and recurrence.end_at else now
        )
        self.end_at.setEnabled(False)
        self.end_enabled.toggled.connect(self.end_at.setEnabled)
        self.active = QCheckBox("Повторение активно")
        self.active.setChecked(recurrence.is_active if recurrence else True)

        self.days = []
        weekdays = QHBoxLayout()
        for day in range(1, 8):
            check = QCheckBox(("Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс")[day - 1])
            check.setProperty("day", day)
            check.toggled.connect(self._clear_error)
            self.days.append(check)
            weekdays.addWidget(check)
        if recurrence and recurrence.days_of_week:
            for check in self.days:
                check.setChecked(check.property("day") in recurrence.days_of_week)

        self.layout.addWidget(FormField("Частота", self.frequency))
        self.layout.addWidget(FormField("Повторять каждые N", self.interval))
        self.layout.addWidget(FormField("День месяца", self.day_of_month))
        self.layout.addWidget(FormField("Начало", self.start_at))
        self.layout.addWidget(self.end_enabled)
        self.layout.addWidget(FormField("Дата окончания", self.end_at))
        self.layout.addLayout(weekdays)
        self.layout.addWidget(self.active)
        self.error_label = QLabel()
        self.error_label.setProperty("role", "form-error")
        self.error_label.hide()
        self.layout.addWidget(self.error_label)

        if recurrence is not None:
            index = self.frequency.findData(recurrence.frequency)
            if index >= 0:
                self.frequency.setCurrentIndex(index)
            self.interval.setValue(recurrence.interval)
            if recurrence.day_of_month is not None:
                self.day_of_month.setValue(recurrence.day_of_month)
            self.end_enabled.setChecked(recurrence.end_at is not None)

        self.frequency.currentIndexChanged.connect(self._update_visibility)
        self._update_visibility()

        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel = SecondaryButton("Отмена")
        cancel.clicked.connect(self.reject)
        save = PrimaryButton("Сохранить")
        save.clicked.connect(self.accept)
        buttons.addWidget(cancel)
        buttons.addWidget(save)
        self.layout.addLayout(buttons)

    def _update_visibility(self):
        weekly = self.frequency.currentData() == "weekly"
        monthly = self.frequency.currentData() == "monthly"
        for check in self.days:
            check.setVisible(weekly)
        self.day_of_month.setVisible(monthly)

    def _clear_error(self, *_):
        self.error_label.clear()
        self.error_label.hide()

    def accept(self):
        self._clear_error()
        if self.frequency.currentData() == "weekly" and not any(
            check.isChecked() for check in self.days
        ):
            self.error_label.setText("Выберите хотя бы один день недели")
            self.error_label.show()
            return
        if (
            self.end_enabled.isChecked()
            and self.end_at.dateTime() < self.start_at.dateTime()
        ):
            self.error_label.setText("Дата окончания раньше начала")
            self.error_label.show()
            return
        super().accept()

    def payload(self) -> dict:
        frequency = self.frequency.currentData()
        return {
            "frequency": frequency,
            "interval": self.interval.value(),
            "days_of_week": (
                [check.property("day") for check in self.days if check.isChecked()]
                if frequency == "weekly"
                else None
            ),
            "day_of_month": (
                self.day_of_month.value() if frequency == "monthly" else None
            ),
            "start_at": _iso(self.start_at),
            "end_at": _iso(self.end_at) if self.end_enabled.isChecked() else None,
            "is_active": self.active.isChecked(),
        }
