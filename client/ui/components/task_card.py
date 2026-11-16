from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
)

from client.core.constants import (
    PRIORITY_BADGES,
    PRIORITY_LABELS,
)

from .badge import Badge


class TaskCard(QFrame):
    """Строка задачи в списке."""

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

    def _on_toggled(self, checked: bool):
        self.task["done"] = checked

        self.setProperty("done", "true" if checked else "false")
        self.style().unpolish(self)
        self.style().polish(self)

        self._apply_done_style(checked)

    def _apply_done_style(self, done: bool):
        font = self.title_label.font()
        font.setStrikeOut(done)
        self.title_label.setFont(font)


class KanbanCard(QFrame):
    """Компактная карточка задачи для канбан-доски."""

    def __init__(self, task: dict, parent=None):
        super().__init__(parent)

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
