from datetime import date, datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from client.api.client import ApiClient
from client.api.mapper import task_view
from client.api.models import Task
from client.core.worker import run_async
from client.services.projects import ProjectService
from client.services.tasks import TaskService
from client.ui.components import (
    EmptyState,
    PrimaryButton,
    SecondaryButton,
    TaskCard,
)
from client.ui.crud_actions import TaskActionsMixin
from client.ui.error_handler import error_message
from client.ui.icons import make_icon

from .base_page import BasePage, clear_layout

FILTERS = [
    ("all", "Все"),
    ("today", "Сегодня"),
    ("active", "Активные"),
    ("overdue", "Просроченные"),
    ("done", "Выполненные"),
]


def matches_filter(task: dict, key: str) -> bool:
    if key == "all":
        return True

    if key == "done":
        return bool(task.get("done"))

    if key == "active":
        return not task.get("done")

    due_at = task.get("due_at")

    if due_at is None:
        return False

    if key == "today":
        return due_at.date() == date.today()  # noqa: DTZ011

    if key == "overdue":
        return not task.get("done") and due_at < datetime.now().astimezone()

    return True


class TasksPage(TaskActionsMixin, BasePage):
    def __init__(
        self,
        api: ApiClient,
        user_id: int | None = None,
        parent=None,
    ):
        super().__init__("Задачи", "Все задачи вашей команды")

        self.api = api
        self.user_id = user_id

        self.task_service = TaskService(api)
        self.project_service = ProjectService(api)

        self.all_tasks: list[dict] = []
        self._task_models: dict[int, Task] = {}
        self._task_cards: dict[int, TaskCard] = {}
        self._pending_task_id: int | None = None
        self._tasks_loaded = False
        self.active_filter = "all"
        self.projects: list = []

        self.project_combo = QComboBox()
        self.project_combo.setMinimumWidth(220)
        self.project_combo.setToolTip("Фильтр по проекту")
        self.project_combo.currentIndexChanged.connect(self._on_project_changed)
        self.add_action(self.project_combo)

        self.tag_combo = QComboBox()
        self.tag_combo.setMinimumWidth(150)
        self.tag_combo.setToolTip("Фильтр по тегу")
        self.tag_combo.addItem("Все теги", None)
        self.tag_combo.currentIndexChanged.connect(
            lambda _index: self._render_tasks()
        )
        self.add_action(self.tag_combo)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("SearchInput")
        self.search_input.setPlaceholderText("Поиск задач")
        self.search_input.setFixedWidth(190)
        self.search_input.addAction(
            make_icon("search"),
            QLineEdit.ActionPosition.LeadingPosition,
        )
        self.search_input.textChanged.connect(
            lambda _text: self._render_tasks()
        )
        self.add_action(self.search_input)

        create_button = PrimaryButton("Новая задача", "plus")
        create_button.clicked.connect(self._create_task)
        self.add_action(create_button)

        self._build_filters()

        self.tasks_container = QWidget()
        self.tasks_layout = QVBoxLayout(self.tasks_container)
        self.tasks_layout.setContentsMargins(0, 0, 0, 0)
        self.tasks_layout.setSpacing(10)

        self.content_layout.addWidget(self.tasks_container)
        self.content_layout.addStretch()

    def _build_filters(self):
        layout = QHBoxLayout()
        layout.setSpacing(8)

        self.filter_group = QButtonGroup(self)
        self.filter_group.setExclusive(True)
        self.filter_group.idClicked.connect(self._on_filter_changed)

        for index, (key, label) in enumerate(FILTERS):
            chip = QPushButton(label)
            chip.setCheckable(True)
            chip.setCursor(Qt.CursorShape.PointingHandCursor)
            chip.setProperty("chip", "true")
            chip.setChecked(index == 0)

            self.filter_group.addButton(chip, index)
            layout.addWidget(chip)

        layout.addStretch()

        self.content_layout.addLayout(layout)

    # ------------------------------------------------------------------
    # Данные
    # ------------------------------------------------------------------

    def reload(self):
        self._tasks_loaded = False

        clear_layout(self.tasks_layout)
        self.tasks_layout.addWidget(EmptyState("Загрузка..."))

        run_async(self._load, self._set_tasks, self._show_error)

    def _load(self) -> dict:
        tasks_data = self.task_service.list()
        projects = self.project_service.list()

        project_names = {project.id: project.name for project in projects}
        subtask_parent_ids = {
            task.parent_task_id
            for task in tasks_data
            if task.parent_task_id is not None
        }
        views = []
        for task in tasks_data:
            if task.parent_task_id is not None:
                continue
            view = task_view(task, project_names)
            view["project_id"] = task.project_id
            view["has_subtasks"] = task.id in subtask_parent_ids
            views.append(view)

        return {
            "views": views,
            "models": {
                task.id: task
                for task in tasks_data
                if task.parent_task_id is None
            },
            "projects": projects,
        }

    def _show_error(self, error: Exception):
        clear_layout(self.tasks_layout)

        self.tasks_layout.addWidget(EmptyState(error_message(error)))

        retry = SecondaryButton("Повторить")
        retry.clicked.connect(self.reload)
        self.tasks_layout.addWidget(retry, 0, Qt.AlignmentFlag.AlignHCenter)

    # ------------------------------------------------------------------
    # Фильтры и отрисовка
    # ------------------------------------------------------------------

    def _on_filter_changed(self, index: int):
        if 0 <= index < len(FILTERS):
            self.active_filter = FILTERS[index][0]
            self._render_tasks()

    def _on_project_changed(self, _index: int):
        self._refresh_tag_filter()
        self._render_tasks()

    def _refresh_tag_filter(self):
        project_id = self.project_combo.currentData()
        tags = sorted({
            str(tag)
            for task in self.all_tasks
            if project_id is None or task.get("project_id") == project_id
            for tag in task.get("tags", [])
            if tag
        }, key=str.casefold)
        selected = self.tag_combo.currentData()
        self.tag_combo.blockSignals(True)
        self.tag_combo.clear()
        self.tag_combo.addItem("Все теги", None)
        for tag in tags:
            self.tag_combo.addItem(f"#{tag}", tag)
        index = self.tag_combo.findData(selected)
        self.tag_combo.setCurrentIndex(max(index, 0))
        self.tag_combo.blockSignals(False)

    def _set_tasks(self, data: dict):
        self._tasks_loaded = True
        self._task_models = data["models"]
        self.all_tasks = data["views"]
        self.projects = data["projects"]

        selected_project_id = self.project_combo.currentData()
        self.project_combo.blockSignals(True)
        self.project_combo.clear()
        self.project_combo.addItem("Все проекты", None)
        for project in self.projects:
            if isinstance(project, dict):
                project_id = project.get("id")
                project_name = project.get("name", "Без названия")
            else:
                project_id = project.id
                project_name = project.name
            self.project_combo.addItem(project_name, project_id)

        index = self.project_combo.findData(selected_project_id)
        self.project_combo.setCurrentIndex(max(index, 0))
        self.project_combo.blockSignals(False)
        self._refresh_tag_filter()
        self._render_tasks()

    def _render_tasks(self):
        clear_layout(self.tasks_layout)
        self._task_cards = {}

        project_id = self.project_combo.currentData()
        selected_tag = self.tag_combo.currentData()
        query = self.search_input.text().strip().casefold()
        filtered = [
            task
            for task in self.all_tasks
            if (project_id is None or task.get("project_id") == project_id)
            and matches_filter(task, self.active_filter)
            and (selected_tag is None or selected_tag in task.get("tags", []))
            and (
                not query
                or query in " ".join(
                    [
                        str(task.get("title") or ""),
                        str(task.get("description") or ""),
                        str(task.get("project") or ""),
                        " ".join(str(tag) for tag in task.get("tags", [])),
                    ]
                ).casefold()
            )
        ]

        if not filtered:
            self.tasks_layout.addWidget(EmptyState("Задач нет"))
            self._focus_task()
            return

        for task in filtered:
            card = TaskCard(task)
            self._task_cards[int(task["id"])] = card

            card.activated.connect(card.toggle_editor)
            card.completion_changed.connect(self.toggle_task)
            card.delete_requested.connect(self.delete_task)
            card.panel_requested.connect(self.open_task_panel)
            card.set_panel_enabled(True)
            card.save_requested.connect(
                lambda task_id, fields, card=card: self.save_task_inline(
                    task_id, fields, card
                )
            )

            self.tasks_layout.addWidget(card)

        self._focus_task()

    # ------------------------------------------------------------------
    # Навигация к конкретной задаче
    # ------------------------------------------------------------------

    def _create_task(self):
        self.open_task_dialog(project_id=self.project_combo.currentData())

    def show_task(self, task_id: int):
        """Переключает фильтр на 'Все' и прокручивает к задаче."""
        self._pending_task_id = task_id
        self.active_filter = "all"
        self.project_combo.setCurrentIndex(0)

        # Переключаем чипс-фильтр
        for index, (key, _) in enumerate(FILTERS):
            if key == "all":
                self.filter_group.button(index).setChecked(True)
                break

        self._render_tasks()

    def _focus_task(self):
        if self._pending_task_id is None or not self._tasks_loaded:
            return

        card = self._task_cards.get(self._pending_task_id)
        self._pending_task_id = None

        if card is not None:
            self.scroll_to_widget(card)
