from PySide6.QtCore import QDateTime, Qt, Signal
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
    QToolButton,
    QVBoxLayout,
)

from client.api.mapper import format_due, parse_datetime
from client.core.constants import (
    PRIORITY_BADGES,
    PRIORITY_LABELS,
    STATUS_DONE,
    STATUS_LABELS,
    STATUS_TODO,
    TASK_PRIORITIES,
    TASK_STATUSES,
)

from .badge import Badge

TAG_VARIANTS = ("primary", "success", "warning", "danger", "purple", "neutral")
TAG_COLOR_VARIANTS = {
    "blue": "primary",
    "green": "success",
    "orange": "warning",
    "red": "danger",
    "purple": "purple",
    "teal": "primary",
}


class _TaskEditor(QFrame):
    save_requested = Signal(dict)
    delete_requested = Signal()

    def __init__(self, task: dict, parent=None):
        super().__init__(parent)
        self.setProperty("component", "card")
        self._has_subtasks = bool(task.get("has_subtasks"))
        self._original_status = task.get("status", "")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self.title = QLineEdit(task.get("title", ""))
        self.title.setPlaceholderText("Название задачи")
        self.error_label = QLabel()
        self.error_label.setProperty("role", "form-error")
        self.error_label.hide()
        self.description = QPlainTextEdit(task.get("description") or "")
        self.description.setPlaceholderText("Описание")
        self.description.setFixedHeight(64)

        selectors = QHBoxLayout()
        self.status = QComboBox()
        for value in TASK_STATUSES:
            self.status.addItem(STATUS_LABELS[value], value)
        self.status.setCurrentIndex(
            max(self.status.findData(task.get("status", "todo")), 0)
        )
        if task.get("has_subtasks"):
            done_index = self.status.findData(STATUS_DONE)
            if done_index >= 0:
                self.status.model().item(done_index).setEnabled(False)
        self.priority = QComboBox()
        for value in TASK_PRIORITIES:
            self.priority.addItem(PRIORITY_LABELS[value], value)
        self.priority.setCurrentIndex(
            max(self.priority.findData(task.get("priority", "medium")), 0)
        )
        selectors.addWidget(self.status)
        selectors.addWidget(self.priority)

        due_row = QHBoxLayout()
        self.no_due = QCheckBox("Без дедлайна")
        self.due_at = QDateTimeEdit()
        self.due_at.setCalendarPopup(True)
        self.due_at.setDisplayFormat("dd.MM.yyyy HH:mm")
        due = parse_datetime(task.get("due_at"))
        self.no_due.setChecked(due is None)
        if due is not None:
            self.due_at.setDateTime(QDateTime(due))
        self.due_at.setEnabled(due is not None)
        self.no_due.toggled.connect(lambda checked: self.due_at.setDisabled(checked))
        due_row.addWidget(self.due_at, 1)
        due_row.addWidget(self.no_due)

        actions = QHBoxLayout()
        save = QPushButton("Сохранить")
        save.clicked.connect(self.save)
        delete = QPushButton("Удалить задачу")
        delete.clicked.connect(lambda: self.delete_requested.emit())
        actions.addStretch()
        actions.addWidget(delete)
        actions.addWidget(save)

        layout.addWidget(self.title)
        layout.addWidget(self.error_label)
        layout.addWidget(self.description)
        layout.addLayout(selectors)
        layout.addLayout(due_row)
        layout.addLayout(actions)

    def save(self):
        title = self.title.text().strip()
        if not title:
            self.error_label.setText("Введите название задачи")
            self.error_label.show()
            self.title.setFocus()
            return
        if (
            self._has_subtasks
            and self.status.currentData() == STATUS_DONE
            and self._original_status != STATUS_DONE
        ):
            self.show_validation_error(
                "Нельзя завершить задачу, пока у неё есть подзадачи"
            )
            return
        self.error_label.hide()
        due_at = None
        if not self.no_due.isChecked():
            due_at = self.due_at.dateTime().toPython().astimezone().isoformat()
        self.save_requested.emit(
            {
                "title": title,
                "description": self.description.toPlainText().strip() or None,
                "status": self.status.currentData(),
                "priority": self.priority.currentData(),
                "due_at": due_at,
            }
        )

    def show_validation_error(self, message: str):
        self.error_label.setText(message)
        self.error_label.show()

    def set_has_subtasks(self, has_subtasks: bool):
        self._has_subtasks = has_subtasks
        done_index = self.status.findData(STATUS_DONE)
        if done_index >= 0:
            self.status.model().item(done_index).setEnabled(not has_subtasks)


class TaskCard(QFrame):
    """Строка задачи с раскрываемым встроенным редактором."""

    activated = Signal(int)
    completion_changed = Signal(int, bool)
    save_requested = Signal(int, dict)
    delete_requested = Signal(int)
    panel_requested = Signal(int, str)

    def __init__(self, task: dict, parent=None):
        super().__init__(parent)

        self.task = task
        self._editing_enabled = True
        self.setProperty("component", "task")
        self.setProperty("done", "true" if task.get("done") else "false")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        content = QHBoxLayout()
        content.setSpacing(12)
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(bool(task.get("done")))
        has_subtasks = bool(task.get("has_subtasks"))
        self.checkbox.setEnabled(not has_subtasks or bool(task.get("done")))
        if has_subtasks:
            self.checkbox.setToolTip(
                "Нельзя завершить задачу, пока у неё есть подзадачи"
            )
        self.checkbox.toggled.connect(self._on_toggled)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        self.title_label = QLabel(task.get("title", ""))
        self.title_label.setProperty("role", "task-title")
        self.title_label.setWordWrap(True)

        title_row = QHBoxLayout()
        title_row.setSpacing(6)
        title_row.addWidget(self.title_label)
        self.tag_badges = self._tag_badges(task)
        for badge in self.tag_badges:
            title_row.addWidget(badge)
        title_row.addStretch()
        self.title_row = title_row

        meta_layout = QHBoxLayout()
        meta_layout.setSpacing(6)
        project = task.get("project")
        if project:
            meta_layout.addWidget(Badge(project, "neutral"))
        meta_layout.addStretch()
        text_layout.addLayout(title_row)
        text_layout.addLayout(meta_layout)

        content.addWidget(self.checkbox, 0, Qt.AlignmentFlag.AlignTop)
        content.addLayout(text_layout, 1)
        self.priority_label, self.due_label = self._add_metadata(content, task)
        self.more_button = self._more_button()
        self.more_button.clicked.connect(self.toggle_editor)
        content.addWidget(self.more_button, 0, Qt.AlignmentFlag.AlignTop)
        self.content_layout = content
        layout.addLayout(content)

        self.editor = _TaskEditor(task, self)
        self.editor.save_requested.connect(
            lambda fields: self.save_requested.emit(self._task_id(), fields)
        )
        self.editor.delete_requested.connect(
            lambda: self.delete_requested.emit(self._task_id())
        )
        self.editor.hide()
        layout.addWidget(self.editor)
        self._build_inline_panels(layout)
        self._apply_done_style(bool(task.get("done")))

    @staticmethod
    def _tag_badges(task: dict) -> list[Badge]:
        colors = task.get("tag_colors", {})
        badges = []
        used = set()
        for index, tag in enumerate(task.get("tags", [])):
            color = colors.get(tag) if isinstance(colors, dict) else None
            variant = TAG_COLOR_VARIANTS.get(color)
            if variant not in TAG_VARIANTS or variant in used:
                variant = next(
                    (item for item in TAG_VARIANTS if item not in used),
                    TAG_VARIANTS[index % len(TAG_VARIANTS)],
                )
            used.add(variant)
            badges.append(Badge(f"#{tag}", variant))
        return badges

    def _build_inline_panels(self, layout: QVBoxLayout):
        controls = QHBoxLayout()
        controls.setSpacing(8)
        self.panel_buttons = {}
        self.panel_containers = {}
        self.inline_panels = {}
        self.loaded_panels = set()
        for key, label in (
            ("subtasks", "Подзадачи"),
            ("comments", "Комментарии"),
            ("reminders", "Напоминания"),
            ("tags", "Теги"),
        ):
            button = QToolButton()
            button.setText(f"{label} ▾")
            button.setToolTip(f"Показать раздел «{label.lower()}»")
            button.clicked.connect(
                lambda _checked=False, panel=key: self.toggle_panel(panel)
            )
            controls.addWidget(button)
            self.panel_buttons[key] = button
            container = QFrame()
            container.setProperty("component", "card")
            container_layout = QVBoxLayout(container)
            container_layout.setContentsMargins(10, 10, 10, 10)
            self.panel_containers[key] = container
            self.inline_panels[key] = container_layout
            container.hide()
            layout.addWidget(container)
        controls.addStretch()
        layout.insertLayout(1, controls)

    def set_panel_enabled(self, enabled: bool):
        for button in self.panel_buttons.values():
            button.setEnabled(enabled)

    def set_editing_enabled(self, enabled: bool):
        self._editing_enabled = enabled
        self.more_button.setVisible(enabled)
        if not enabled:
            self.editor.hide()
        for button in self.panel_buttons.values():
            button.setVisible(enabled)

    def set_inline_panel(self, key: str, panel):
        if key not in self.inline_panels:
            return
        container_layout = self.inline_panels[key]
        while container_layout.count():
            item = container_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        container_layout.addWidget(panel)
        self.panel_containers[key].show()

    def update_tags(self, tags: list[str], colors: dict[str, str] | None = None):
        self.task["tags"] = tags
        self.task["tag_colors"] = colors or {}
        for badge in self.tag_badges:
            self.title_row.removeWidget(badge)
            badge.deleteLater()
        self.tag_badges = self._tag_badges(self.task)
        index = self.title_row.indexOf(self.title_label) + 1
        for badge in self.tag_badges:
            self.title_row.insertWidget(index, badge)
            index += 1

    def toggle_panel(self, key: str):
        if not self._editing_enabled:
            return
        container = self.panel_containers[key]
        if key in self.loaded_panels:
            container.setVisible(container.isHidden())
            return
        self.loaded_panels.add(key)
        self.panel_requested.emit(self._task_id(), key)

    @staticmethod
    def _more_button() -> QToolButton:
        button = QToolButton()
        button.setText("⋯")
        button.setToolTip("Изменить задачу")
        button.setProperty("icon", "true")
        return button

    @staticmethod
    def _add_metadata(layout: QHBoxLayout, task: dict):
        priority = task.get("priority")
        priority_label = None
        if priority:
            priority_label = Badge(
                PRIORITY_LABELS.get(priority, priority),
                PRIORITY_BADGES.get(priority, "neutral"),
            )
            layout.addWidget(priority_label, 0, Qt.AlignmentFlag.AlignTop)
        due_label = None
        if task.get("due"):
            due_label = QLabel(task["due"])
            due_label.setProperty("role", "muted")
            layout.addWidget(due_label, 0, Qt.AlignmentFlag.AlignTop)
        return priority_label, due_label

    def update_task(self, fields: dict):
        self.task.update(fields)
        self.task["due"] = format_due(fields.get("due_at"))
        self.task["done"] = fields.get("status") == "done"
        self.title_label.setText(fields["title"])
        self.checkbox.blockSignals(True)
        self.checkbox.setChecked(self.task["done"])
        self.checkbox.blockSignals(False)
        self.checkbox.setEnabled(
            not self.task.get("has_subtasks") or self.task["done"]
        )
        self._apply_done_style(self.task["done"])
        if self.due_label is not None:
            self.due_label.setText(self.task["due"])
        elif self.task["due"]:
            self.due_label = QLabel(self.task["due"])
            self.due_label.setProperty("role", "muted")
            self.content_layout.insertWidget(
                self.content_layout.indexOf(self.more_button),
                self.due_label,
                0,
                Qt.AlignmentFlag.AlignTop,
            )
        if self.priority_label is not None:
            priority = fields.get("priority", "")
            self.priority_label.setText(PRIORITY_LABELS.get(priority, priority))
            self.priority_label.set_variant(
                PRIORITY_BADGES.get(priority, "neutral")
            )

    def toggle_editor(self, _task_id: int | None = None):
        if not self._editing_enabled:
            return
        self.editor.setVisible(self.editor.isHidden())

    def show_edit_error(self, message: str):
        self.editor.show_validation_error(message)

    def set_done(self, done: bool):
        self.task["done"] = done
        self.task["status"] = STATUS_DONE if done else STATUS_TODO
        self.setProperty("done", "true" if done else "false")
        self.checkbox.blockSignals(True)
        self.checkbox.setChecked(done)
        self.checkbox.blockSignals(False)
        self.checkbox.setEnabled(not self.task.get("has_subtasks") or done)
        self._apply_done_style(done)
        self.style().unpolish(self)
        self.style().polish(self)

    def set_has_subtasks(self, has_subtasks: bool):
        self.task["has_subtasks"] = has_subtasks
        if has_subtasks:
            self.checkbox.setToolTip(
                "Нельзя завершить задачу, пока у неё есть подзадачи"
            )
        else:
            self.checkbox.setToolTip("")
        self.checkbox.setEnabled(not has_subtasks or bool(self.task.get("done")))
        self.editor.set_has_subtasks(has_subtasks)

    def _task_id(self) -> int:
        return int(self.task.get("id") or 0)

    def _on_toggled(self, checked: bool):
        if checked and self.task.get("has_subtasks"):
            self.set_done(False)
            return
        self.task["done"] = checked
        self.task["status"] = STATUS_DONE if checked else STATUS_TODO
        self.checkbox.setEnabled(not self.task.get("has_subtasks") or checked)
        self.setProperty("done", "true" if checked else "false")
        self.style().unpolish(self)
        self.style().polish(self)
        self._apply_done_style(checked)
        self.completion_changed.emit(self._task_id(), checked)

    def mouseDoubleClickEvent(self, event):
        self.activated.emit(self._task_id())
        super().mouseDoubleClickEvent(event)

    def _apply_done_style(self, done: bool):
        font = self.title_label.font()
        font.setStrikeOut(done)
        self.title_label.setFont(font)


class KanbanCard(QFrame):
    """Карточка канбана с возможностью изменить только статус."""

    status_changed = Signal(int, str, str)

    def __init__(self, task: dict, parent=None):
        super().__init__(parent)
        self.task = task
        self.setProperty("component", "task")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        header = QHBoxLayout()
        title = QLabel(task.get("title", ""))
        title.setProperty("role", "task-title")
        title.setWordWrap(True)
        self.title_label = title
        header.addWidget(title)
        self.tag_badges = TaskCard._tag_badges(task)
        for badge in self.tag_badges:
            header.addWidget(badge)
        header.addStretch()

        footer = QHBoxLayout()
        priority = task.get("priority")
        self.priority_label = None
        if priority:
            self.priority_label = Badge(
                PRIORITY_LABELS.get(priority, priority),
                PRIORITY_BADGES.get(priority, "neutral"),
            )
            footer.addWidget(self.priority_label)
        footer.addStretch()
        due = task.get("due")
        self.due_label = None
        if due:
            due_label = QLabel(due)
            due_label.setProperty("role", "muted")
            footer.addWidget(due_label)

        footer.addWidget(QLabel("Статус"))
        self.status_combo = QComboBox()
        for value in TASK_STATUSES:
            self.status_combo.addItem(STATUS_LABELS[value], value)
        self.status_combo.setCurrentIndex(
            max(self.status_combo.findData(task.get("status", "todo")), 0)
        )
        self._set_done_status_enabled(not task.get("has_subtasks"))
        self.status_combo.currentIndexChanged.connect(self._on_status_changed)
        footer.addWidget(self.status_combo)

        layout.addLayout(header)
        layout.addLayout(footer)

    def _set_done_status_enabled(self, enabled: bool):
        done_index = self.status_combo.findData(STATUS_DONE)
        if done_index >= 0:
            self.status_combo.model().item(done_index).setEnabled(enabled)

    def _on_status_changed(self, _index: int):
        status = self.status_combo.currentData()
        old_status = self.task.get("status", "todo")
        if status == old_status:
            return
        if status == STATUS_DONE and self.task.get("has_subtasks"):
            self.set_status(old_status)
            return
        self.task["status"] = status
        self.status_changed.emit(self._task_id(), status, old_status)

    def _task_id(self) -> int:
        return int(self.task.get("id") or 0)

    def set_status(self, status: str):
        self.status_combo.blockSignals(True)
        self.status_combo.setCurrentIndex(
            max(self.status_combo.findData(status), 0)
        )
        self.status_combo.blockSignals(False)
        self.task["status"] = status

    def set_status_enabled(self, enabled: bool):
        self.status_combo.setEnabled(enabled)
