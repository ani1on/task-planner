from datetime import datetime, timedelta

from PySide6.QtCore import QDateTime, QLocale, Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateTimeEdit,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from client.api.errors import NotFoundError
from client.api.mapper import format_due, format_relative
from client.api.models import (
    Checklist,
    ChecklistItem,
    Comment,
    Member,
    Task,
)
from client.core.constants import (
    PRIORITY_BADGES,
    PRIORITY_LABELS,
    STATUS_BADGES,
    STATUS_DONE,
    STATUS_LABELS,
    STATUS_TODO,
)
from client.services.checklists import ChecklistService
from client.services.comments import CommentService
from client.services.reminders import ReminderService
from client.services.tags import TagService
from client.services.tasks import TaskService
from client.ui.components import (
    Badge,
    FormField,
    PrimaryButton,
    SecondaryButton,
    SectionTitle,
    TextInput,
)

from .recurrence import FREQUENCIES
from .reminders import ReminderManagerPanel
from .tag_manager import TagManagementPanel


def _clear(layout):
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()

        if widget is not None:
            widget.deleteLater()
            continue

        child = item.layout()
        if child is not None:
            _clear(child)


def _muted(text: str) -> QLabel:
    label = QLabel(text)
    label.setProperty("role", "muted")

    return label


def _icon_button(text: str, tooltip: str) -> QPushButton:
    button = QPushButton(text)
    button.setProperty("icon", "true")
    button.setToolTip(tooltip)
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    button.setFixedSize(26, 26)

    return button


class _Section(QWidget):
    """Раздел диалога: контент и строка ошибки."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(8)

        self.error_label = QLabel()
        self.error_label.setProperty("role", "form-error")
        self.error_label.setWordWrap(True)
        self.error_label.hide()

        self.layout.addWidget(self.error_label)

    def clear_error(self):
        self.error_label.clear()
        self.error_label.hide()

    def show_error(self, error: Exception):
        from client.ui.error_handler import error_message

        self.error_label.setText(error_message(error))
        self.error_label.show()

    def reload(self):
        """Перезагружает содержимое раздела."""


class SubtasksSection(_Section):
    """Подзадачи: отметка выполнения, добавление и удаление."""

    subtasks_changed = Signal(bool)

    def __init__(self, task_service: TaskService, task_id: int, parent=None):
        super().__init__(parent)

        self.task_service = task_service
        self.task_id = task_id
        self.has_subtasks: bool | None = None

        self.progress_label = QLabel()
        self.progress_label.setProperty("role", "muted")

        self.items = QVBoxLayout()
        self.items.setSpacing(6)

        self.input = TextInput("Новая подзадача")
        self.input.returnPressed.connect(self.add)

        add_button = SecondaryButton("Добавить")
        add_button.clicked.connect(self.add)

        row = QHBoxLayout()
        row.setSpacing(8)
        row.addWidget(self.input, 1)
        row.addWidget(add_button)

        self.layout.addWidget(self.progress_label)
        self.layout.addLayout(self.items)
        self.layout.addLayout(row)

        self.reload()

    def reload(self):
        self.clear_error()
        _clear(self.items)

        try:
            subtasks = self.task_service.subtasks(self.task_id)
        except Exception as error:
            self.show_error(error)
            return

        done = sum(1 for subtask in subtasks if subtask.is_done)
        self.has_subtasks = bool(subtasks)
        self.subtasks_changed.emit(self.has_subtasks)
        self.progress_label.setText(f"Выполнено {done} из {len(subtasks)}")

        if not subtasks:
            self.items.addWidget(_muted("Подзадач пока нет"))
            return

        for subtask in subtasks:
            self.items.addWidget(self._row(subtask))

    def _row(self, subtask: Task) -> QWidget:
        row = QWidget()

        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        checkbox = QCheckBox()
        checkbox.setChecked(subtask.is_done)
        checkbox.toggled.connect(
            lambda checked, task_id=subtask.id: self.toggle(task_id, checked),
        )

        title_input = TextInput()
        title_input.setText(subtask.title)
        edit = _icon_button("✓", "Сохранить подзадачу")
        edit.clicked.connect(
            lambda _=False, task_id=subtask.id, field=title_input: self.edit(
                task_id, field
            ),
        )

        remove = _icon_button("×", "Удалить подзадачу")
        remove.clicked.connect(
            lambda _=False, task_id=subtask.id: self.remove(task_id),
        )

        layout.addWidget(checkbox)
        layout.addWidget(title_input, 1)
        layout.addWidget(edit)
        layout.addWidget(remove)

        return row

    def add(self):
        title = self.input.text().strip()

        if not title:
            return

        self.clear_error()

        try:
            self.task_service.create_subtask(self.task_id, title)
        except Exception as error:
            self.show_error(error)
            return

        self.input.clear()
        self.reload()

    def toggle(self, task_id: int, done: bool):
        self.clear_error()

        try:
            self.task_service.update(
                task_id,
                status=STATUS_DONE if done else STATUS_TODO,
            )
        except Exception as error:
            self.show_error(error)
            return

        self.reload()

    def edit(self, task_id: int, field: QLineEdit):
        new_title = field.text().strip()
        if not new_title:
            return

        self.clear_error()

        try:
            self.task_service.update(task_id, title=new_title)
        except Exception as error:
            self.show_error(error)
            return

        self.reload()

    def remove(self, task_id: int):
        self.clear_error()

        try:
            self.task_service.delete(task_id)
        except Exception as error:
            self.show_error(error)
            return

        self.reload()


class ChecklistsSection(_Section):
    """Чек-листы задачи: пункты, прогресс, добавление и удаление."""

    def __init__(
        self,
        checklist_service: ChecklistService,
        task_id: int,
        parent=None,
    ):
        super().__init__(parent)

        self.checklist_service = checklist_service
        self.task_id = task_id

        self.checklists_layout = QVBoxLayout()
        self.checklists_layout.setSpacing(10)

        self.title_input = TextInput("Название чек-листа")
        self.title_input.returnPressed.connect(self.add_checklist)

        add_button = SecondaryButton("Добавить чек-лист")
        add_button.clicked.connect(self.add_checklist)

        row = QHBoxLayout()
        row.setSpacing(8)
        row.addWidget(self.title_input, 1)
        row.addWidget(add_button)

        self.layout.addLayout(self.checklists_layout)
        self.layout.addLayout(row)

        self.reload()

    def reload(self):
        self.clear_error()
        _clear(self.checklists_layout)

        try:
            checklists = self.checklist_service.list_with_items(self.task_id)
        except Exception as error:
            self.show_error(error)
            return

        if not checklists:
            self.checklists_layout.addWidget(_muted("Чек-листов пока нет"))
            return

        for checklist, items in checklists:
            self.checklists_layout.addWidget(self._card(checklist, items))

    def edit_checklist(self, checklist_id: int, field: QLineEdit):
        title = field.text().strip()
        if not title:
            return
        self.clear_error()
        try:
            self.checklist_service.update(checklist_id, title=title)
        except Exception as error:
            self.show_error(error)
            return
        self.reload()

    def _card(
        self,
        checklist: Checklist,
        items: list[ChecklistItem],
    ) -> QFrame:
        frame = QFrame()
        frame.setProperty("component", "card")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        done = sum(1 for item in items if item.is_completed)

        header = QHBoxLayout()
        header.setSpacing(8)

        title = TextInput()
        title.setText(checklist.title)

        progress = QLabel(f"{done} из {len(items)}")
        progress.setProperty("role", "muted")

        edit = _icon_button("✓", "Сохранить название чек-листа")
        edit.clicked.connect(
            lambda _=False, checklist_id=checklist.id, field=title:
                self.edit_checklist(checklist_id, field)
        )
        remove = _icon_button("×", "Удалить чек-лист")
        remove.clicked.connect(
            lambda _=False, checklist_id=checklist.id: self.remove_checklist(
                checklist_id
            ),
        )

        header.addWidget(title)
        header.addWidget(progress)
        header.addStretch()
        header.addWidget(edit)
        header.addWidget(remove)

        layout.addLayout(header)

        for item in items:
            layout.addWidget(self._item_row(item))

        field = TextInput("Новый пункт")

        add_button = _icon_button("+", "Добавить пункт")
        add_button.clicked.connect(
            lambda _=False, checklist_id=checklist.id, field=field: self.add_item(
                checklist_id, field
            ),
        )

        add_row = QHBoxLayout()
        add_row.setSpacing(6)
        add_row.addWidget(field, 1)
        add_row.addWidget(add_button)

        layout.addLayout(add_row)

        return frame

    def _item_row(self, item: ChecklistItem) -> QWidget:
        row = QWidget()

        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        checkbox = QCheckBox()
        checkbox.setChecked(item.is_completed)
        checkbox.toggled.connect(
            lambda checked, item_id=item.id: self.toggle_item(item_id, checked),
        )

        content = TextInput()
        content.setText(item.content)
        edit = _icon_button("✓", "Сохранить пункт")
        edit.clicked.connect(
            lambda _=False, item_id=item.id, field=content: self.edit_item(
                item_id, field
            ),
        )

        remove = _icon_button("×", "Удалить пункт")
        remove.clicked.connect(
            lambda _=False, item_id=item.id: self.remove_item(item_id),
        )

        layout.addWidget(checkbox)
        layout.addWidget(content, 1)
        layout.addWidget(edit)
        layout.addWidget(remove)

        return row

    def add_checklist(self):
        title = self.title_input.text().strip()

        if not title:
            return

        self.clear_error()

        try:
            self.checklist_service.create(self.task_id, title)
        except Exception as error:
            self.show_error(error)
            return

        self.title_input.clear()
        self.reload()

    def remove_checklist(self, checklist_id: int):
        self.clear_error()

        try:
            self.checklist_service.delete(checklist_id)
        except Exception as error:
            self.show_error(error)
            return

        self.reload()

    def add_item(self, checklist_id: int, field: TextInput):
        content = field.text().strip()

        if not content:
            return

        self.clear_error()

        try:
            self.checklist_service.add_item(checklist_id, content)
        except Exception as error:
            self.show_error(error)
            return

        field.clear()
        self.reload()

    def toggle_item(self, item_id: int, checked: bool):
        self.clear_error()

        try:
            self.checklist_service.update_item(item_id, is_completed=checked)
        except Exception as error:
            self.show_error(error)
            return

        self.reload()

    def edit_item(self, item_id: int, field: QLineEdit):
        content = field.text().strip()
        if not content:
            return

        self.clear_error()

        try:
            self.checklist_service.update_item(item_id, content=content)
        except Exception as error:
            self.show_error(error)
            return

        self.reload()

    def remove_item(self, item_id: int):
        self.clear_error()

        try:
            self.checklist_service.delete_item(item_id)
        except Exception as error:
            self.show_error(error)
            return

        self.reload()


class TagsSection(_Section):
    """Теги задачи: назначение из тегов проекта и снятие."""

    tags_changed = Signal(list)

    def __init__(
        self,
        tag_service: TagService,
        task_id: int,
        project_id: int,
        parent=None,
    ):
        super().__init__(parent)

        self.tag_service = tag_service
        self.task_id = task_id
        self.project_id = project_id

        self.chips = QHBoxLayout()
        self.chips.setSpacing(6)

        self.combo = QComboBox()
        self.combo.setMinimumWidth(150)

        self.add_button = SecondaryButton("Добавить")
        self.add_button.clicked.connect(self.add)

        self.create_button = SecondaryButton("Новый тег")
        self.create_button.clicked.connect(self.create_tag)
        self.new_tag_input = TextInput("Название нового тега")
        self.manage_button = SecondaryButton("Управлять")
        self.manage_button.clicked.connect(self.manage_tags)
        self.management_panel = None

        row = QHBoxLayout()
        row.setSpacing(8)
        row.addWidget(self.combo, 1)
        row.addWidget(self.add_button)
        row.addWidget(self.new_tag_input)
        row.addWidget(self.create_button)
        row.addWidget(self.manage_button)

        self.layout.addLayout(self.chips)
        self.layout.addLayout(row)

        self.reload()

    def reload(self):
        self.clear_error()
        _clear(self.chips)
        self.combo.clear()

        try:
            task_tags = self.tag_service.task_tags(self.task_id)
            project_tags = self.tag_service.list(self.project_id)
        except Exception as error:
            self.show_error(error)
            return

        self.tags_changed.emit(task_tags)
        task_tag_ids = {tag.id for tag in task_tags}

        if not task_tags:
            self.chips.addWidget(_muted("Тегов у задачи нет"))
        else:
            for tag in task_tags:
                button = QPushButton(f"#{tag.name}")
                button.setProperty("chip", "true")
                button.setCursor(Qt.CursorShape.PointingHandCursor)
                button.setToolTip("Убрать тег")
                button.clicked.connect(
                    lambda _=False, tag_id=tag.id: self.remove(tag_id),
                )

                self.chips.addWidget(button)

        self.chips.addStretch()

        available = [
            tag for tag in project_tags if tag.id not in task_tag_ids
        ]

        for tag in available:
            self.combo.addItem(tag.name, tag.id)

        if not project_tags:
            self.combo.addItem("В проекте нет тегов", None)

        self.add_button.setEnabled(bool(available))

    def create_tag(self):
        name = self.new_tag_input.text().strip()

        if not name:
            return

        self.clear_error()

        try:
            self.tag_service.create(self.project_id, name)
        except Exception as error:
            self.show_error(error)
            return

        self.new_tag_input.clear()
        self.reload()

    def add(self):
        tag_id = self.combo.currentData()

        if tag_id is None:
            return

        self.clear_error()

        try:
            self.tag_service.add_to_task(self.task_id, tag_id)
        except Exception as error:
            self.show_error(error)
            return

        self.reload()

    def manage_tags(self):
        if self.management_panel is None:
            self.management_panel = TagManagementPanel(
                self.tag_service,
                self.project_id,
                self,
            )
            self.management_panel.changed.connect(self.reload)
            self.layout.addWidget(self.management_panel)
        else:
            self.management_panel.setVisible(self.management_panel.isHidden())

    def remove(self, tag_id: int):
        self.clear_error()

        try:
            self.tag_service.remove_from_task(self.task_id, tag_id)
        except Exception as error:
            self.show_error(error)
            return

        self.reload()


class CommentsSection(_Section):
    """Комментарии: список, добавление и удаление своих."""

    def __init__(
        self,
        comment_service: CommentService,
        task_id: int,
        members: list[Member],
        current_user_id: int | None,
        parent=None,
    ):
        super().__init__(parent)

        self.comment_service = comment_service
        self.task_id = task_id
        self.current_user_id = current_user_id
        self.authors = {member.user_id: member.nick_name for member in members}

        self.list_layout = QVBoxLayout()
        self.list_layout.setSpacing(10)

        self.input = QPlainTextEdit()
        self.input.setPlaceholderText("Написать комментарий")
        self.input.setFixedHeight(72)

        send_button = PrimaryButton("Отправить")
        send_button.clicked.connect(self.add)

        row = QHBoxLayout()
        row.setSpacing(8)
        row.addWidget(self.input, 1)
        row.addWidget(send_button, 0, Qt.AlignmentFlag.AlignBottom)

        self.layout.addLayout(self.list_layout)
        self.layout.addLayout(row)

        self.reload()

    def reload(self):
        self.clear_error()
        _clear(self.list_layout)

        try:
            comments = self.comment_service.list(self.task_id)
        except Exception as error:
            self.show_error(error)
            return

        if not comments:
            self.list_layout.addWidget(_muted("Комментариев пока нет"))
            return

        for comment in comments:
            self.list_layout.addWidget(self._card(comment))

    def _card(self, comment: Comment) -> QFrame:
        frame = QFrame()
        frame.setProperty("component", "card")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        header = QHBoxLayout()
        header.setSpacing(8)

        author = QLabel(self._author_name(comment.author_id))
        author.setProperty("role", "task-title")

        moment = QLabel(format_relative(comment.created_at))
        moment.setProperty("role", "muted")

        header.addWidget(author)
        header.addWidget(moment)
        header.addStretch()

        if (
            self.current_user_id is not None
            and comment.author_id == self.current_user_id
        ):
            content = QPlainTextEdit(comment.content)
            content.setFixedHeight(72)
            edit = _icon_button("✓", "Сохранить комментарий")
            edit.clicked.connect(
                lambda _=False, comment_id=comment.id, editor=content: self.edit(
                    comment_id, editor
                ),
            )

            remove = _icon_button("×", "Удалить комментарий")
            remove.clicked.connect(
                lambda _=False, comment_id=comment.id: self.remove(comment_id),
            )

            header.addWidget(edit)
            header.addWidget(remove)
        else:
            content = QLabel(comment.content)
            content.setWordWrap(True)

        layout.addLayout(header)
        layout.addWidget(content)

        return frame

    def _author_name(self, author_id: int) -> str:
        return self.authors.get(author_id, f"Пользователь #{author_id}")

    def add(self):
        text = self.input.toPlainText().strip()

        if not text:
            return

        self.clear_error()

        try:
            self.comment_service.create(self.task_id, text)
        except Exception as error:
            self.show_error(error)
            return

        self.input.clear()
        self.reload()

    def edit(self, comment_id: int, editor: QPlainTextEdit):
        content = editor.toPlainText().strip()
        if not content:
            return

        self.clear_error()

        try:
            self.comment_service.update(comment_id, content)
        except Exception as error:
            self.show_error(error)
            return

        self.reload()

    def remove(self, comment_id: int):
        self.clear_error()

        try:
            self.comment_service.delete(comment_id)
        except Exception as error:
            self.show_error(error)
            return

        self.reload()


class RecurrenceSection(_Section):
    """Настройка повтора и создание следующего вхождения задачи."""

    occurrence_created = Signal(object)

    def __init__(
        self,
        task_service: TaskService,
        task_id: int,
        parent=None,
        default_start_at: datetime | None = None,
    ):
        super().__init__(parent)
        self.task_service = task_service
        self.task_id = task_id
        self.recurrence = None
        self.default_start_at = default_start_at or datetime.now().astimezone()

        self.summary = QLabel()
        self.summary.setProperty("role", "muted")
        self.frequency = QComboBox()
        for label, value in FREQUENCIES:
            self.frequency.addItem(label, value)
        self.interval = QSpinBox()
        self.interval.setRange(1, 365)
        self.interval.setValue(1)
        self.day_of_month = QSpinBox()
        self.day_of_month.setRange(1, 31)
        self.day_of_month.setValue(self.default_start_at.day)
        self.frequency_field = FormField("Частота", self.frequency)
        self.interval_field = FormField("Интервал", self.interval)
        self.day_field = FormField("День месяца", self.day_of_month)
        self.start_at = self._date_edit(self.default_start_at)
        self.start_field = FormField("Начало", self.start_at)
        self.end_enabled = QCheckBox("Завершить повторение")
        self.end_at = self._date_edit(
            self.default_start_at + timedelta(days=365)
        )
        self.end_at.setEnabled(False)
        self.end_field = FormField("Дата окончания", self.end_at)
        self.end_enabled.toggled.connect(self.end_at.setEnabled)
        self.active = QCheckBox("Повторение активно")
        self.active.setChecked(True)
        self.days = []
        weekdays = QHBoxLayout()
        for day, label in enumerate(("Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"), 1):
            check = QCheckBox(label)
            check.setProperty("day", day)
            self.days.append(check)
            weekdays.addWidget(check)
        self.frequency.currentIndexChanged.connect(self._update_visibility)

        self.configure_button = SecondaryButton("Сохранить повторение")
        self.configure_button.clicked.connect(self.configure)
        self.next_button = SecondaryButton("Создать следующую")
        self.next_button.clicked.connect(self.create_next)
        self.remove_button = SecondaryButton("Отключить")
        self.remove_button.clicked.connect(self.remove)

        row = QHBoxLayout()
        row.addWidget(self.configure_button)
        row.addWidget(self.next_button)
        row.addWidget(self.remove_button)
        self.layout.addWidget(self.summary)
        self.layout.addWidget(self.frequency_field)
        self.layout.addWidget(self.interval_field)
        self.layout.addWidget(self.day_field)
        self.layout.addWidget(self.start_field)
        self.layout.addWidget(self.end_enabled)
        self.layout.addWidget(self.end_field)
        self.layout.addLayout(weekdays)
        self.layout.addWidget(self.active)
        self.layout.addLayout(row)
        self._update_visibility()
        self.reload()

    @staticmethod
    def _date_edit(value: datetime) -> QDateTimeEdit:
        edit = QDateTimeEdit(QDateTime(value))
        edit.setCalendarPopup(True)
        edit.setDisplayFormat("dd.MM.yyyy HH:mm")
        edit.setLocale(QLocale("ru_RU"))
        edit.calendarWidget().setFirstDayOfWeek(Qt.DayOfWeek.Monday)
        return edit

    def _update_visibility(self):
        weekly = self.frequency.currentData() == "weekly"
        monthly = self.frequency.currentData() == "monthly"
        self.day_field.setVisible(monthly)
        for check in self.days:
            check.setVisible(weekly)

    def reload(self):
        self.clear_error()
        try:
            self.recurrence = self.task_service.recurrence(self.task_id)
        except NotFoundError:
            self.recurrence = None
        except Exception as error:
            self.show_error(error)
            return

        if self.recurrence is None:
            self.summary.setText("Повторение не настроено")
            self.next_button.setEnabled(False)
            self.remove_button.setEnabled(False)
            self.active.setChecked(True)
            return

        index = self.frequency.findData(self.recurrence.frequency)
        if index >= 0:
            self.frequency.setCurrentIndex(index)
        self.interval.setValue(self.recurrence.interval)
        if self.recurrence.day_of_month is not None:
            self.day_of_month.setValue(self.recurrence.day_of_month)
        self.start_at.setDateTime(QDateTime(self.recurrence.start_at))
        self.end_enabled.setChecked(self.recurrence.end_at is not None)
        if self.recurrence.end_at is not None:
            self.end_at.setDateTime(QDateTime(self.recurrence.end_at))
        for check in self.days:
            check.setChecked(
                check.property("day") in (self.recurrence.days_of_week or ())
            )
        self.active.setChecked(self.recurrence.is_active)
        frequency_labels = {
            "daily": "Ежедневно",
            "weekly": "Еженедельно",
            "monthly": "Ежемесячно",
        }
        summary = (
            f"{frequency_labels.get(self.recurrence.frequency, self.recurrence.frequency)}, "
            f"интервал {self.recurrence.interval}"
        )
        if self.recurrence.next_run_at is not None:
            summary += f" · следующая: {format_due(self.recurrence.next_run_at)}"
        if not self.recurrence.is_active:
            summary += " · отключено"
        self.summary.setText(summary)
        can_create_next = (
            self.recurrence.is_active
            and self.recurrence.next_run_at is not None
            and (
                self.recurrence.end_at is None
                or self.recurrence.next_run_at <= self.recurrence.end_at
            )
        )
        self.next_button.setEnabled(can_create_next)
        self.remove_button.setEnabled(True)
        self._update_visibility()

    def configure(self):
        self.clear_error()
        frequency = self.frequency.currentData()
        if frequency == "weekly" and not any(check.isChecked() for check in self.days):
            self.show_error(ValueError("Выберите хотя бы один день недели"))
            return
        start_at = self.start_at.dateTime().toPython().astimezone()
        end_at = (
            self.end_at.dateTime().toPython().astimezone()
            if self.end_enabled.isChecked()
            else None
        )
        if end_at is not None and end_at < start_at:
            self.show_error(ValueError("Дата окончания раньше начала"))
            return
        fields = {
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
            "start_at": start_at.isoformat(),
            "end_at": end_at.isoformat() if end_at else None,
            "is_active": self.active.isChecked(),
        }
        try:
            if self.recurrence is None:
                self.task_service.set_recurrence(
                    self.task_id,
                    **fields,
                )
            else:
                self.task_service.update_recurrence(
                    self.task_id,
                    **fields,
                )
        except Exception as error:
            self.show_error(error)
            return
        self.reload()

    def create_next(self):
        try:
            task = self.task_service.create_next_occurrence(self.task_id)
        except Exception as error:
            self.show_error(error)
            return
        self.occurrence_created.emit(task)

    def remove(self):
        try:
            self.task_service.delete_recurrence(self.task_id)
        except Exception as error:
            self.show_error(error)
            return
        self.reload()


class TaskDetailPanel(QWidget):
    """Встроенная карточка задачи с дополнительными рабочими разделами."""

    close_requested = Signal()

    def __init__(
        self,
        task: Task,
        project_name: str,
        members: list[Member],
        current_user_id: int | None,
        task_service: TaskService,
        tag_service: TagService,
        checklist_service: ChecklistService,
        comment_service: CommentService,
        reminder_service: ReminderService,
        parent=None,
    ):
        super().__init__(parent)
        self.setProperty("component", "card")

        self.task = task
        self.project_name = project_name
        self.members = list(members)

        self.task_service = task_service

        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(12, 12, 12, 12)
        self.root_layout.setSpacing(14)

        self._build_header()
        self._build_body(
            tag_service=tag_service,
            checklist_service=checklist_service,
            comment_service=comment_service,
            current_user_id=current_user_id,
            reminder_service=reminder_service,
        )
        self._build_footer()

        self._refresh_header()

    # ------------------------------------------------------------------
    # Построение
    # ------------------------------------------------------------------

    def _build_header(self):
        header = QWidget()

        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(6)

        self.title_label = QLabel()
        self.title_label.setProperty("role", "card-title")
        self.title_label.setWordWrap(True)

        self.badges = QHBoxLayout()
        self.badges.setSpacing(6)

        text_layout.addWidget(self.title_label)
        text_layout.addLayout(self.badges)

        layout.addLayout(text_layout, 1)
        close_button = SecondaryButton("Свернуть")
        close_button.clicked.connect(lambda: self.close_requested.emit())
        layout.addWidget(close_button, 0, Qt.AlignmentFlag.AlignTop)

        self.root_layout.addWidget(header)

    def _build_body(
        self,
        tag_service: TagService,
        checklist_service: ChecklistService,
        comment_service: CommentService,
        current_user_id: int | None,
        reminder_service: ReminderService,
    ):
        scroll = QScrollArea()
        scroll.setObjectName("PageScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        body = QWidget()
        body.setObjectName("PageBody")

        body_layout = QVBoxLayout(body)
        self.body_layout = body_layout
        body_layout.setContentsMargins(0, 0, 6, 0)
        body_layout.setSpacing(14)

        self.meta_label = QLabel()
        self.meta_label.setWordWrap(True)

        self.description_label = QLabel()
        self.description_label.setWordWrap(True)
        self.description_label.setProperty("role", "muted")

        body_layout.addWidget(self.meta_label)
        body_layout.addWidget(self.description_label)

        self.subtasks = SubtasksSection(self.task_service, self.task.id)
        self.tags = TagsSection(tag_service, self.task.id, self.task.project_id)
        self.comments = CommentsSection(
            comment_service=comment_service,
            task_id=self.task.id,
            members=self.members,
            current_user_id=current_user_id,
        )
        self.reminders_button = SecondaryButton("Напоминания")
        self.reminders_button.clicked.connect(
            lambda: self._manage_reminders(reminder_service)
        )
        self.reminders_panel = None

        for title, section in (
            ("Подзадачи", self.subtasks),
            ("Теги", self.tags),
            ("Комментарии", self.comments),
        ):
            body_layout.addWidget(SectionTitle(title))
            body_layout.addWidget(section)

        body_layout.addWidget(self.reminders_button)
        body_layout.addStretch()

        scroll.setWidget(body)

        self.root_layout.addWidget(scroll, 1)

    def _manage_reminders(self, service: ReminderService):
        if self.reminders_panel is None:
            self.reminders_panel = ReminderManagerPanel(
                service,
                task_id=self.task.id,
                parent=self,
            )
            self.body_layout.addWidget(self.reminders_panel)
        else:
            self.reminders_panel.setVisible(self.reminders_panel.isHidden())

    def _build_footer(self):
        close_button = SecondaryButton("Свернуть")
        close_button.clicked.connect(lambda: self.close_requested.emit())

        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(close_button)

        self.root_layout.addLayout(row)

    # ------------------------------------------------------------------
    # Обновление заголовка
    # ------------------------------------------------------------------

    def _refresh_header(self):
        self.title_label.setText(self.task.title)

        _clear(self.badges)

        if self.project_name:
            self.badges.addWidget(Badge(self.project_name, "neutral"))

        self.badges.addWidget(
            Badge(
                STATUS_LABELS.get(self.task.status, self.task.status),
                STATUS_BADGES.get(self.task.status, "neutral"),
            )
        )
        self.badges.addWidget(
            Badge(
                PRIORITY_LABELS.get(self.task.priority, self.task.priority),
                PRIORITY_BADGES.get(self.task.priority, "neutral"),
            )
        )
        self.badges.addStretch()

        assignee = self._member_name(self.task.assignee_id)

        self.meta_label.setText(
            f"Исполнитель: {assignee or 'не назначен'}\n"
            f"Начало: {format_due(self.task.start_at) or 'не задано'}\n"
            f"Дедлайн: {format_due(self.task.due_at) or 'не задано'}"
        )

        self.description_label.setText(
            self.task.description or "Описание не заполнено"
        )

    def _member_name(self, user_id: int | None) -> str | None:
        for member in self.members:
            if member.user_id == user_id:
                return member.nick_name

        return None

    # ------------------------------------------------------------------
