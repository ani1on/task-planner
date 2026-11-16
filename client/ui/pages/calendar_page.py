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
        self.year = self.today.year
        self.month = self.today.month

        self._events: list[dict] = []

        previous = SecondaryButton("<")
        previous.setToolTip("Предыдущий месяц")

        next_button = SecondaryButton(">")
        next_button.setToolTip("Следующий месяц")

        previous.clicked.connect(lambda: self._shift_month(-1))
        next_button.clicked.connect(lambda: self._shift_month(1))

        self.month_label = QLabel()
        self.month_label.setProperty("role", "card-title")

        self.add_action(previous)
        self.add_action(self.month_label)
        self.add_action(next_button)

        self._render(self.year, self.month)

    # ------------------------------------------------------------------
    # Данные
    # ------------------------------------------------------------------

    def reload(self):
        if self.demo or self.task_service is None:
            self._events = [
                {**event, "month": self.today.month, "year": self.today.year}
                for event in upcoming_events()
            ]
            self._render(self.year, self.month)
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
        self._render(self.year, self.month)

    # ------------------------------------------------------------------
    # Навигация
    # ------------------------------------------------------------------

    def _shift_month(self, delta: int):
        month = self.month + delta
        year = self.year

        if month < 1:
            month = 12
            year -= 1
        elif month > 12:
            month = 1
            year += 1

        self._render(year, month)

    # ------------------------------------------------------------------
    # Отрисовка
    # ------------------------------------------------------------------

    def _render(self, year: int, month: int):
        self.clear_content()

        self.year = year
        self.month = month
        self.month_label.setText(f"{MONTHS[month - 1]} {year}")

        grid = QGridLayout()
        grid.setSpacing(8)

        for column, weekday in enumerate(WEEKDAYS):
            label = QLabel(weekday)
            label.setProperty("role", "muted")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            grid.addWidget(label, 0, column)

        for row, week in enumerate(calendar.monthcalendar(year, month), start=1):
            for column, day in enumerate(week):
                if day == 0:
                    continue

                grid.addWidget(self._build_cell(day), row, column)

        self.content_layout.addLayout(grid)
        self.content_layout.addStretch()

    def _month_events(self, day: int) -> list[dict]:
        return [
            event
            for event in self._events
            if event.get("day") == day
            and event.get("month", self.month) == self.month
            and event.get("year", self.year) == self.year
        ]

    def _build_cell(self, day: int) -> QFrame:
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

        for event in self._month_events(day)[:MAX_EVENTS]:
            label = QLabel(event["title"])
            label.setProperty("role", "muted")
            layout.addWidget(label)

        layout.addStretch()

        return cell
