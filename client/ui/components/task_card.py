from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QVBoxLayout,
)

from client.core.constants import (
    PRIORITY_BADGES,
    PRIORITY_LABELS,
)

from .badge import Badge


def _task_menu(parent, task: dict) -> tuple[QMenu, dict]:
    menu = QMenu(parent)

    edit = menu.addAction("Редактировать")

    if task.get("done"):
        toggle = menu.addAction("Вернуть в работу")
    else:
        toggle = menu.addAction("Отметить выполненной")

    menu.addSeparator()
    delete = menu.addAction("Удалить")

    return menu, {
        edit: "edit",
        toggle: "toggle",
        delete: "delete",
    }


class TaskCard(QFrame):
    """Строка задачи в списке."""

    activated = Signal(int)
    completion_changed = Signal(int, bool)
    edit_requested = Signal(int)
    delete_requested = Signal(int)

    def __init__(self, task: dict, parent=None):
        super().__init__(parent)

        self.task = task

        self.setProperty("component", "task")
        self.setProperty("done", "true" if task.get("done") else "false")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(12)

        self.checkbox = QCheckBox()
        self.checkbox.setChecked(bool(task.get("done")))
        self.checkbox.toggled.connect(self._on_toggled)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)

        self.title_label = QLabel(task.get("title", ""))
        self.title_label.setProperty("role", "task-title")
        self.title_label.setWordWrap(True)

        meta_layout = QHBoxLayout()
        meta_layout.setSpacing(6)

        project = task.get("project")
        if project:
            meta_layout.addWidget(Badge(project, "neutral"))

        for tag in task.get("tags", []):
            meta_layout.addWidget(Badge(f"#{tag}", "neutral"))

        meta_layout.addStretch()

        text_layout.addWidget(self.title_label)
        text_layout.addLayout(meta_layout)

        layout.addWidget(self.checkbox, 0, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(text_layout, 1)

        priority = task.get("priority")
        if priority:
            layout.addWidget(
                Badge(
                    PRIORITY_LABELS.get(priority, priority),
                    PRIORITY_BADGES.get(priority, "neutral"),
                ),
                0,
                Qt.AlignmentFlag.AlignTop,
            )

        due = task.get("due")
        if due:
            due_label = QLabel(due)
            due_label.setProperty("role", "muted")
            layout.addWidget(due_label, 0, Qt.AlignmentFlag.AlignTop)

        self._apply_done_style(bool(task.get("done")))

    # ------------------------------------------------------------------
    # Взаимодействие
    # ------------------------------------------------------------------

    def _task_id(self) -> int:
        return int(self.task.get("id") or 0)

    def _on_toggled(self, checked: bool):
        self.task["done"] = checked

        self.setProperty("done", "true" if checked else "false")
        self.style().unpolish(self)
        self.style().polish(self)

        self._apply_done_style(checked)

        self.completion_changed.emit(self._task_id(), checked)

    def mouseDoubleClickEvent(self, event):
        self.activated.emit(self._task_id())

        super().mouseDoubleClickEvent(event)

    def contextMenuEvent(self, event):
        menu, actions = _task_menu(self, self.task)
        action = menu.exec(event.globalPos())
        kind = actions.get(action)

        if kind == "edit":
            self.edit_requested.emit(self._task_id())
        elif kind == "toggle":
            self.completion_changed.emit(
                self._task_id(),
                not self.task.get("done"),
            )
        elif kind == "delete":
            self.delete_requested.emit(self._task_id())

    def _apply_done_style(self, done: bool):
        font = self.title_label.font()
        font.setStrikeOut(done)
        self.title_label.setFont(font)


class KanbanCard(QFrame):
    """Компактная карточка задачи для канбан-доски."""

    activated = Signal(int)
    edit_requested = Signal(int)
    delete_requested = Signal(int)

    def __init__(self, task: dict, parent=None):
        super().__init__(parent)

        self.task = task

        self.setProperty("component", "task")
        self.setProperty("clickable", "true")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        title = QLabel(task.get("title", ""))
        title.setProperty("role", "task-title")
        title.setWordWrap(True)

        footer = QHBoxLayout()
        footer.setSpacing(6)

        priority = task.get("priority")
        if priority:
            footer.addWidget(
                Badge(
                    PRIORITY_LABELS.get(priority, priority),
                    PRIORITY_BADGES.get(priority, "neutral"),
                )
            )

        footer.addStretch()

        due = task.get("due")
        if due:
            due_label = QLabel(due)
            due_label.setProperty("role", "muted")
            footer.addWidget(due_label)

        layout.addWidget(title)
        layout.addLayout(footer)

    def _task_id(self) -> int:
        return int(self.task.get("id") or 0)

    def mouseDoubleClickEvent(self, event):
        self.activated.emit(self._task_id())

        super().mouseDoubleClickEvent(event)

    def contextMenuEvent(self, event):
        menu, actions = _task_menu(self, self.task)
        action = menu.exec(event.globalPos())
        kind = actions.get(action)

        if kind == "edit":
            self.edit_requested.emit(self._task_id())
        elif kind == "delete":
            self.delete_requested.emit(self._task_id())
