from datetime import datetime, timedelta

from PySide6.QtCore import QDateTime, QLocale, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDateTimeEdit,
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from client.api.models import Reminder
from client.services.reminders import ReminderService
from client.ui.components import PrimaryButton, SecondaryButton
from client.ui.error_handler import handle_api_error

CHANNELS = (
    ("На компьютере", "desktop"),
    ("В приложении", "in_app"),
    ("Электронная почта", "email"),
)
STATUSES = ("pending", "sent", "cancelled")


def _datetime_edit(value: datetime) -> QDateTimeEdit:
    editor = QDateTimeEdit(QDateTime(value))
    editor.setCalendarPopup(True)
    editor.setDisplayFormat("dd.MM.yyyy HH:mm")
    editor.setLocale(QLocale("ru_RU"))
    editor.calendarWidget().setFirstDayOfWeek(Qt.DayOfWeek.Monday)
    return editor


class ReminderManagerPanel(QWidget):
    """Встроенный просмотр и редактор напоминаний одного объекта."""

    def __init__(
        self,
        service: ReminderService,
        *,
        task_id: int | None = None,
        event_id: int | None = None,
        parent=None,
    ):
        super().__init__(parent)
        if (task_id is None) == (event_id is None):
            raise ValueError("Укажите задачу или событие для напоминаний")
        self.service = service
        self.task_id = task_id
        self.event_id = event_id
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(8)

        self.items_layout = QVBoxLayout()
        self.items_layout.setSpacing(8)
        self.root_layout.addLayout(self.items_layout)

        form = QHBoxLayout()
        self.new_date = _datetime_edit(
            datetime.now().astimezone() + timedelta(hours=1)
        )
        self.new_channel = self._channel_combo()
        add = PrimaryButton("Добавить")
        add.clicked.connect(self.add)
        form.addWidget(self.new_date, 1)
        form.addWidget(self.new_channel)
        form.addWidget(add)
        self.root_layout.addLayout(form)
        self.reload()

    @staticmethod
    def _channel_combo(selected: str = "desktop") -> QComboBox:
        combo = QComboBox()
        for label, value in CHANNELS:
            combo.addItem(label, value)
        index = combo.findData(selected)
        combo.setCurrentIndex(max(index, 0))
        return combo

    def _list(self) -> list[Reminder]:
        if self.task_id is not None:
            return self.service.list(task_id=self.task_id)
        return self.service.list(event_id=self.event_id)

    def reload(self):
        while self.items_layout.count():
            item = self.items_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        try:
            reminders = self._list()
        except Exception as error:
            handle_api_error(error, self)
            return

        if not reminders:
            self.items_layout.addWidget(QLabel("Напоминаний пока нет"))
            return
        for reminder in reminders:
            self.items_layout.addWidget(self._row(reminder))

    def _row(self, reminder: Reminder) -> QFrame:
        frame = QFrame()
        frame.setProperty("component", "card")
        row = QHBoxLayout(frame)

        date = _datetime_edit(reminder.remind_at)
        channel = self._channel_combo(reminder.channel)
        status = QComboBox()
        status.addItems(STATUSES)
        status.setCurrentText(reminder.status)

        save = SecondaryButton("Сохранить")
        save.clicked.connect(
            lambda _=False, item=reminder, date_editor=date, channel_combo=channel,
            status_combo=status: self.update(
                item.id,
                date_editor,
                channel_combo,
                status_combo,
            )
        )
        delete = SecondaryButton("Удалить")
        delete.clicked.connect(
            lambda _=False, reminder_id=reminder.id: self.remove(reminder_id)
        )

        row.addWidget(date, 1)
        row.addWidget(channel)
        row.addWidget(status)
        row.addWidget(save)
        row.addWidget(delete)
        return frame

    def add(self):
        value = self.new_date.dateTime().toPython()
        try:
            self.service.create(
                value,
                task_id=self.task_id,
                event_id=self.event_id,
                channel=self.new_channel.currentData(),
            )
        except Exception as error:
            handle_api_error(error, self)
            return
        self.reload()

    def update(
        self,
        reminder_id: int,
        date: QDateTimeEdit,
        channel: QComboBox,
        status: QComboBox,
    ):
        try:
            self.service.update(
                reminder_id,
                remind_at=date.dateTime().toPython(),
                channel=channel.currentData(),
                status=status.currentText(),
            )
        except Exception as error:
            handle_api_error(error, self)
            return
        self.reload()

    def remove(self, reminder_id: int):
        try:
            self.service.delete(reminder_id)
        except Exception as error:
            handle_api_error(error, self)
            return
        self.reload()
