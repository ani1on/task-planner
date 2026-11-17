import calendar
from datetime import date, datetime, time

from PySide6.QtCore import QDateTime, Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateTimeEdit,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
)

from client.api.client import ApiClient
from client.api.models import Event, Project, Task
from client.core.constants import PRIORITY_LABELS
from client.core.worker import run_async
from client.services.events import EventService
from client.services.projects import ProjectService
from client.services.reminders import ReminderService
from client.services.tasks import TaskService
from client.ui.components import PrimaryButton, SecondaryButton
from client.ui.crud_actions import TaskActionsMixin
from client.ui.dialogs import ConfirmDialog, EventDialog
from client.ui.dialogs.reminders import ReminderManagerPanel
from client.ui.dialogs.task_detail import RecurrenceSection
from client.ui.error_handler import error_message

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

MAX_EVENTS = 3


class _EventEditor(QFrame):
    save_requested = Signal(int, dict)
    delete_requested = Signal(int)

    def __init__(
        self,
        event: Event,
        projects: list[Project],
        reminder_service: ReminderService | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self._event = event
        self.setProperty("component", "card")
        layout = QVBoxLayout(self)
        self.root_layout = layout
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        self.title = QLineEdit(event.title)
        self.title.setPlaceholderText("Название события")
        self.project = QComboBox()
        self.project.addItem("Без проекта", None)
        for project in projects:
            self.project.addItem(project.name, project.id)
        self.project.setCurrentIndex(
            max(self.project.findData(event.project_id), 0)
        )
        self.start = self._date_edit(event.start_at)
        self.end = self._date_edit(event.end_at)
        dates = QHBoxLayout()
        dates.addWidget(self.start)
        dates.addWidget(self.end)
        self.all_day = QCheckBox("Весь день")
        self.all_day.setChecked(event.all_day)
        self.location = QLineEdit(event.location or "")
        self.location.setPlaceholderText("Место проведения")
        self.description = QPlainTextEdit(event.description or "")
        self.description.setPlaceholderText("Описание")
        self.description.setFixedHeight(72)
        self.error_label = QLabel()
        self.error_label.setProperty("role", "form-error")
        self.error_label.hide()

        actions = QHBoxLayout()
        delete = QPushButton("Удалить событие")
        delete.clicked.connect(
            lambda: self.delete_requested.emit(self._event.id)
        )
        save = QPushButton("Сохранить")
        save.clicked.connect(self.save)
        actions.addStretch()
        actions.addWidget(delete)
        actions.addWidget(save)

        layout.addWidget(QLabel("Название"))
        layout.addWidget(self.title)
        layout.addWidget(self.project)
        layout.addLayout(dates)
        layout.addWidget(self.all_day)
        layout.addWidget(self.location)
        layout.addWidget(self.description)
        layout.addWidget(self.error_label)
        layout.addLayout(actions)
        self.reminders_panel = None
        if reminder_service is not None:
            reminders = QPushButton("Напоминания")
            reminders.clicked.connect(
                lambda: self._toggle_reminders(reminder_service)
            )
            layout.addWidget(reminders)

    def _toggle_reminders(self, service: ReminderService):
        if self.reminders_panel is None:
            self.reminders_panel = ReminderManagerPanel(
                service,
                event_id=self._event.id,
                parent=self,
            )
            self.root_layout.addWidget(self.reminders_panel)
        else:
            self.reminders_panel.setVisible(self.reminders_panel.isHidden())

    @staticmethod
    def _date_edit(value: datetime) -> QDateTimeEdit:
        edit = QDateTimeEdit(QDateTime(value))
        edit.setCalendarPopup(True)
        edit.setDisplayFormat("dd.MM.yyyy HH:mm")
        return edit

    def save(self):
        title = self.title.text().strip()
        if not title:
            self.error_label.setText("Введите название события")
            self.error_label.show()
            return
        if self.end.dateTime() < self.start.dateTime():
            self.error_label.setText("Окончание раньше начала")
            self.error_label.show()
            return
        self.error_label.hide()
        self.save_requested.emit(
            self._event.id,
            {
                "title": title,
                "project_id": self.project.currentData(),
                "start_at": self.start.dateTime().toPython().astimezone().isoformat(),
                "end_at": self.end.dateTime().toPython().astimezone().isoformat(),
                "all_day": self.all_day.isChecked(),
                "location": self.location.text().strip() or None,
                "description": self.description.toPlainText().strip() or None,
            },
        )


class CalendarPage(TaskActionsMixin, BasePage):
    def __init__(self, api: ApiClient, parent=None):
        super().__init__("Календарь", "Задачи и дедлайны по дням")

        self.api = api
        self.task_service = TaskService(api)
        self.project_service = ProjectService(api)
        self.event_service = EventService(api)
        self.reminder_service = ReminderService(api)

        self.today = date.today()  # noqa: DTZ011
        self.year = self.today.year
        self.month = self.today.month

        self._events: list[dict] = []
        self._event_models: dict[int, Event] = {}
        self._task_models: dict[int, Task] = {}
        self._selected_event_id: int | None = None
        self._selected_task_id: int | None = None
        self._projects: list[Project] = []

        previous = SecondaryButton("<")
        previous.setToolTip("Предыдущий месяц")

        today_button = SecondaryButton("Сегодня")
        today_button.clicked.connect(self._go_today)

        next_button = SecondaryButton(">")
        next_button.setToolTip("Следующий месяц")

        previous.clicked.connect(lambda: self._shift_month(-1))
        next_button.clicked.connect(lambda: self._shift_month(1))

        self.month_label = QLabel()
        self.month_label.setProperty("role", "card-title")
        self.month_label.setMinimumWidth(140)
        self.month_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.project_combo = QComboBox()
        self.project_combo.setMinimumWidth(190)
        self.project_combo.setToolTip("Фильтр по проекту")
        self.project_combo.addItem("Все проекты", None)
        self.project_combo.currentIndexChanged.connect(
            lambda _index: self._render(self.year, self.month)
        )

        add_task = PrimaryButton("Задача на сегодня", "plus")
        add_task.clicked.connect(self._create_task_for_today)
        add_event = SecondaryButton("Событие на сегодня")
        add_event.clicked.connect(
            lambda: self._create_event_for_day(self.today),
        )

        self.add_action(previous)
        self.add_action(today_button)
        self.add_action(self.month_label)
        self.add_action(next_button)
        self.add_action(self.project_combo)
        self.add_action(add_task)
        self.add_action(add_event)

        self._render(self.year, self.month)

    # ------------------------------------------------------------------
    # Данные
    # ------------------------------------------------------------------

    def reload(self):
        self.show_loading()
        run_async(self._load_events, self._set_data, self._show_error)

    def _load_events(self) -> dict:
        tasks_data = self.task_service.list()
        task_models = {
            task.id: task
            for task in tasks_data
            if task.parent_task_id is None
        }
        projects = self.project_service.list()
        range_start = datetime(self.year, self.month, 1).astimezone()
        if self.month == 12:
            range_end = datetime(self.year + 1, 1, 1).astimezone()
        else:
            range_end = datetime(self.year, self.month + 1, 1).astimezone()
        calendar_events = self.event_service.list(
            date_from=range_start,
            date_to=range_end,
        )

        events: list[dict] = []
        for task in tasks_data:
            if task.parent_task_id is None and task.due_at:
                events.append({
                    "id": task.id,
                    "kind": "task",
                    "day": task.due_at.day,
                    "title": task.title,
                    "time": task.due_at.strftime("%H:%M"),
                    "project_id": task.project_id,
                    "priority": task.priority,
                    "month": task.due_at.month,
                    "year": task.due_at.year,
                })

        event_models = {}
        for event in calendar_events:
            event_models[event.id] = event
            events.append({
                "id": event.id,
                "kind": "event",
                "day": event.start_at.day,
                "title": event.title,
                "time": "" if event.all_day else event.start_at.strftime("%H:%M"),
                "project_id": event.project_id,
                "month": event.start_at.month,
                "year": event.start_at.year,
            })

        return {
            "events": events,
            "projects": projects,
            "event_models": event_models,
            "task_models": task_models,
        }

    def _show_error(self, error: Exception):
        self.show_error(error_message(error), self.reload)

    def _set_data(self, data: dict):
        self._events = data["events"]
        self._event_models = data["event_models"]
        self._task_models = data["task_models"]
        self._projects = data["projects"]
        self._set_projects(data["projects"])
        self._render(self.year, self.month)

    def _set_projects(self, projects: list):
        selected_project_id = self.project_combo.currentData()
        self.project_combo.blockSignals(True)
        self.project_combo.clear()
        self.project_combo.addItem("Все проекты", None)
        for project in projects:
            if isinstance(project, dict):
                project_id = project.get("id")
                project_name = project.get("name", "Без названия")
            else:
                project_id = project.id
                project_name = project.name
            self.project_combo.addItem(project_name, project_id)
        index = self.project_combo.findData(selected_project_id)
        self.project_combo.setCurrentIndex(max(index, 0))
        self.project_combo.setEnabled(bool(projects))

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

        self.year = year
        self.month = month
        self._selected_task_id = None
        self._selected_event_id = None
        self.reload()

    def _go_today(self):
        self.today = date.today()  # noqa: DTZ011
        self.year = self.today.year
        self.month = self.today.month
        self._selected_task_id = None
        self._selected_event_id = None
        self.reload()

    # ------------------------------------------------------------------
    # Создание задач в календаре
    # ------------------------------------------------------------------

    def _create_task_for_today(self):
        self._go_today()
        self._create_task_for_day(self.today.day)

    def _create_task_for_day(self, day: int):
        selected_day = date(self.year, self.month, day)
        due_at = datetime.combine(selected_day, time(9, 0)).astimezone()

        self.open_task_dialog(
            project_id=self.project_combo.currentData(),
            due_at=due_at,
        )

    def _create_event_for_day(self, selected_day: date):
        start_at = datetime.combine(selected_day, time(9, 0)).astimezone()
        dialog = EventDialog(
            self._projects,
            start_at=start_at,
            reminder_service=self.reminder_service,
            parent=self,
        )
        if dialog.exec() != EventDialog.DialogCode.Accepted:
            return
        if dialog.delete_requested:
            return

        try:
            self.event_service.create(**dialog.payload())
        except Exception as error:
            self._show_error(error)
            return

        self.reload()

    def _edit_event(self, event_id: int):
        event = self._event_models.get(event_id)
        if event is None:
            self.reload()
            return
        self._selected_task_id = None
        self._selected_event_id = (
            None if self._selected_event_id == event_id else event_id
        )
        self._render(self.year, self.month)

    def _select_calendar_task(self, task_id: int):
        if task_id not in self._task_models:
            return
        self._selected_event_id = None
        self._selected_task_id = (
            None if self._selected_task_id == task_id else task_id
        )
        self._render(self.year, self.month)

    def _save_event_inline(self, event_id: int, payload: dict):
        run_async(
            self.event_service.update,
            self._after_event_change,
            self._show_error,
            event_id,
            **payload,
        )

    def _delete_event(self, event_id: int):
        if ConfirmDialog("Удалить событие?", self).exec() != (
            ConfirmDialog.DialogCode.Accepted
        ):
            return
        run_async(
            self.event_service.delete,
            self._after_event_change,
            self._show_error,
            event_id,
        )

    def _after_event_change(self, _result):
        self._selected_event_id = None
        self.reload()

    def _task_dialog_saved(self, task: Task):
        self._selected_task_id = task.id
        self._selected_event_id = None
        if task.due_at is not None:
            self.year = task.due_at.year
            self.month = task.due_at.month
        selected_project_id = self.project_combo.currentData()
        if selected_project_id is not None and selected_project_id != task.project_id:
            index = self.project_combo.findData(task.project_id)
            if index >= 0:
                self.project_combo.setCurrentIndex(index)

    def _on_occurrence_created(self, task: Task):
        self._selected_task_id = task.id
        self._selected_event_id = None
        if task.due_at is not None:
            self.year = task.due_at.year
            self.month = task.due_at.month
        selected_project_id = self.project_combo.currentData()
        if selected_project_id is not None and selected_project_id != task.project_id:
            index = self.project_combo.findData(task.project_id)
            if index >= 0:
                self.project_combo.setCurrentIndex(index)
        self.reload()


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
            grid.setColumnStretch(column, 1)

        weeks = calendar.monthcalendar(year, month)
        for row, week in enumerate(weeks, start=1):
            grid.setRowStretch(row, 1)
            for column, day in enumerate(week):
                if day == 0:
                    continue
                grid.addWidget(self._build_cell(day), row, column)

        self.content_layout.addLayout(grid, 1)
        task = self._task_models.get(self._selected_task_id)
        if (
            task is not None
            and task.due_at is not None
            and task.due_at.year == year
            and task.due_at.month == month
        ):
            self.content_layout.addWidget(
                self._build_recurrence_section(task)
            )
        event = self._event_models.get(self._selected_event_id)
        if event is not None:
            editor = _EventEditor(
                event,
                self._projects,
                self.reminder_service,
                self,
            )
            editor.save_requested.connect(self._save_event_inline)
            editor.delete_requested.connect(self._delete_event)
            self.content_layout.addWidget(editor)

    def _build_recurrence_section(self, task: Task) -> RecurrenceSection:
        section = RecurrenceSection(
            self.task_service,
            task.id,
            self,
            default_start_at=task.start_at or task.due_at,
        )
        section.occurrence_created.connect(self._on_occurrence_created)
        return section

    def _month_events(self, day: int) -> list[dict]:
        return sorted(
            (
                event
                for event in self._events
                if event.get("day") == day
                and event.get("month", self.month) == self.month
                and event.get("year", self.year) == self.year
                and (
                    self.project_combo.currentData() is None
                    or event.get("project_id") == self.project_combo.currentData()
                )
            ),
            key=lambda event: event.get("time", ""),
        )

    def _build_cell(self, day: int) -> QFrame:
        cell = QFrame()
        cell.setProperty("component", "calendar-cell")
        cell.setMinimumHeight(116)

        is_today = (
            day == self.today.day
            and self.month == self.today.month
            and self.year == self.today.year
        )
        cell.setProperty("today", "true" if is_today else "false")

        layout = QVBoxLayout(cell)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(5)

        header = QHBoxLayout()
        header.setSpacing(4)

        number = QLabel(str(day))
        number.setProperty("role", "calendar-day")
        header.addWidget(number)
        header.addStretch()

        add_button = QPushButton("+")
        add_button.setObjectName("CalendarAddButton")
        add_button.setFixedSize(28, 28)
        add_button.setCursor(Qt.CursorShape.PointingHandCursor)
        add_button.setToolTip(
            f"Добавить задачу на {day:02d}.{self.month:02d}.{self.year}"
        )
        add_button.clicked.connect(
            lambda _checked=False, selected_day=day: self._show_add_menu(
                add_button, selected_day
            )
        )
        header.addWidget(add_button)

        layout.addLayout(header)

        events = self._month_events(day)
        for event in events[:MAX_EVENTS]:
            text = event.get("title", "Без названия")
            if event.get("time"):
                text = f"{event['time']} · {text}"
            if event.get("kind") == "event":
                title = QPushButton(text)
                title.setProperty("role", "calendar-event")
                title.setFlat(True)
                title.setCursor(Qt.CursorShape.PointingHandCursor)
                title.setToolTip("Открыть событие")
                event_id = event.get("id")
                if event_id is not None:
                    title.clicked.connect(
                        lambda _=False, selected_id=event_id: self._edit_event(
                            selected_id
                        )
                    )
            else:
                title = QPushButton(text)
                priority = event.get("priority", "medium")
                title.setObjectName("CalendarTaskEvent")
                title.setProperty("priority", priority)
                title.setProperty("role", "calendar-event")
                title.setFlat(True)
                title.setCursor(Qt.CursorShape.PointingHandCursor)
                title.setToolTip(
                    "Настроить повторение задачи · "
                    f"важность: {PRIORITY_LABELS.get(priority, priority)}"
                )
                task_id = event.get("id")
                if task_id is not None:
                    title.clicked.connect(
                        lambda _=False, selected_id=task_id: self._select_calendar_task(
                            selected_id
                        )
                    )
            title.setMaximumHeight(34)
            layout.addWidget(title)

        if len(events) > MAX_EVENTS:
            more = QLabel(f"+ ещё {len(events) - MAX_EVENTS}")
            more.setProperty("role", "muted")
            layout.addWidget(more)

        layout.addStretch()
        return cell

    def _show_add_menu(self, button: QPushButton, day: int):
        menu = QMenu(button)
        add_task = menu.addAction("Добавить задачу")
        add_event = menu.addAction("Добавить событие")
        selected = menu.exec(button.mapToGlobal(button.rect().bottomLeft()))
        if selected is add_task:
            self._create_task_for_day(day)
        elif selected is add_event:
            self._create_event_for_day(date(self.year, self.month, day))
