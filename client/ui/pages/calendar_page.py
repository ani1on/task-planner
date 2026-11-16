import calendar
from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QVBoxLayout,
)

from client.api.client import ApiClient
from client.core.worker import run_async
from client.services.tasks import TaskService
from client.ui.components import SecondaryButton
from client.ui.error_handler import error_message
from client.ui.mock_data import upcoming_events

from .base_page import BasePage

WEEKDAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

MONTHS = [
    "Январь",
    "Февраль",
    "Март",
    "Апрель",
    "Май",
    "Июнь",
    "Июль",
    "Август",
    "Сентябрь",
    "Октябрь",
    "Ноябрь",
    "Декабрь",
]

MAX_EVENTS = 2


class CalendarPage(BasePage):
    def __init__(self, api: ApiClient | None = None, demo: bool = False, parent=None):
        super().__init__("Календарь", "Задачи и дедлайны по дням")

        self.api = api
        self.demo = demo
        self.task_service = TaskService(api) if api else None

        self.today = date.today()  # noqa: DTZ011

        previous = SecondaryButton("<")
        next_button = SecondaryButton(">")

        self.month_label = QLabel()
        self.month_label.setProperty("role", "card-title")

        self.add_action(previous)
        self.add_action(self.month_label)
        self.add_action(next_button)

        self.grid = QGridLayout()
        self.grid.setSpacing(8)

        self.content_layout.addLayout(self.grid)
        self.content_layout.addStretch()

        self._render(self.today.year, self.today.month)

    # ------------------------------------------------------------------
    # Данные
    # ------------------------------------------------------------------

    def reload(self):
        if self.demo or self.task_service is None:
            self._render(self.today.year, self.today.month)
            return

        self.show_loading()

        run_async(self._load_events, self._set_events, self._show_error)

    def _load_events(self) -> list[dict]:
        tasks_data = self.task_service.list()

        events: list[dict] = []
        for task in tasks_data:
            if task.due_at:
                events.append({
                    "day": task.due_at.day,
                    "title": task.title,
                    "month": task.due_at.month,
                    "year": task.due_at.year,
                })

        return events

    def _show_error(self, error: Exception):
        self.show_error(error_message(error), self.reload)

    def _set_events(self, events: list[dict]):
        self._events = events
        self._render(self.today.year, self.today.month)

    # ------------------------------------------------------------------
    # Отрисовка
    # ------------------------------------------------------------------

    def _render(self, year: int, month: int):
        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self.year = year
        self.month = month

        self.month_label.setText(f"{MONTHS[month - 1]} {year}")

        for column, weekday in enumerate(WEEKDAYS):
            label = QLabel(weekday)
            label.setProperty("role", "muted")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grid.addWidget(label, 0, column)

        events = getattr(self, "_events", upcoming_events())
        weeks = calendar.monthcalendar(year, month)

        for row, week in enumerate(weeks, start=1):
            for column, day in enumerate(week):
                if day == 0:
                    continue

                cell = self._build_cell(day, events)
                self.grid.addWidget(cell, row, column)

    def _build_cell(self, day: int, events: list[dict]) -> QFrame:
        cell = QFrame()
        cell.setProperty("component", "calendar-cell")
        cell.setMinimumHeight(84)

        is_today = (
            day == self.today.day
            and self.month == self.today.month
            and self.year == self.today.year
        )
        cell.setProperty("today", "true" if is_today else "false")

        layout = QVBoxLayout(cell)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(4)

        number = QLabel(str(day))
        number.setProperty("role", "calendar-day")

        layout.addWidget(number)

        day_events = [
            event
            for event in events
            if event["day"] == day
            and getattr(event, "month", 1) == self.month
            and getattr(event, "year", 9999) == self.year
        ]

        if not day_events:
            pass
        else:
            for event in day_events[:MAX_EVENTS]:
                label = QLabel(event["title"])
                label.setProperty("role", "muted")
                layout.addWidget(label)

        layout.addStretch()

        return cell
