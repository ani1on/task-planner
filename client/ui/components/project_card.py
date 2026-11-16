from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QVBoxLayout,
)

from client.core.constants import (
    PROJECT_COLORS,
    PROJECT_STATUS_LABELS,
)

from .avatar import Avatar
from .badge import Badge
from .progress_bar import ProgressBar


class ProjectCard(QFrame):
    """Карточка проекта с прогрессом и участниками."""

    activated = Signal(int)
    edit_requested = Signal(int)
    archive_requested = Signal(int)
    delete_requested = Signal(int)

    def __init__(self, project: dict, parent=None):
        super().__init__(parent)

        self.project = project

        self.setProperty("component", "card")
        self.setProperty("clickable", "true")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        header = QHBoxLayout()
        header.setSpacing(8)

        color = PROJECT_COLORS.get(project.get("color"), PROJECT_COLORS["blue"])
        dot = QFrame()
        dot.setFixedSize(10, 10)
        dot.setStyleSheet(f"background-color: {color}; border-radius: 5px;")

        name = QLabel(project.get("name", ""))
        name.setProperty("role", "card-title")

        header.addWidget(dot)
        header.addWidget(name)
        header.addStretch()

        status = project.get("status", "active")
        header.addWidget(
            Badge(
                PROJECT_STATUS_LABELS.get(status, status),
                "success" if status == "active" else "neutral",
            )
        )

        description = QLabel(project.get("description", ""))
        description.setProperty("role", "muted")
        description.setWordWrap(True)

        done = project.get("done", 0)
        total = project.get("total", 0)
        percent = int(done / total * 100) if total else 0

        progress = ProgressBar(percent)

        progress_label = QLabel(f"{done} из {total} задач")
        progress_label.setProperty("role", "muted")

        members_layout = QHBoxLayout()
        members_layout.setSpacing(-6)

        for member in project.get("members", []):
            avatar = Avatar(member, size=26)
            members_layout.addWidget(avatar)

        members_layout.addStretch()

        layout.addLayout(header)
        layout.addWidget(description)
        layout.addWidget(progress)
        layout.addWidget(progress_label)
        layout.addLayout(members_layout)

    # ------------------------------------------------------------------
    # Взаимодействие
    # ------------------------------------------------------------------

    def _project_id(self) -> int:
        return int(self.project.get("id") or 0)

    def mouseDoubleClickEvent(self, event):
        self.activated.emit(self._project_id())

        super().mouseDoubleClickEvent(event)

    def contextMenuEvent(self, event):
        menu = QMenu(self)

        edit = menu.addAction("Редактировать")

        if self.project.get("status") == "archived":
            archive = menu.addAction("Вернуть из архива")
        else:
            archive = menu.addAction("В архив")

        menu.addSeparator()
        delete = menu.addAction("Удалить")

        action = menu.exec(event.globalPos())

        if action is edit:
            self.edit_requested.emit(self._project_id())
        elif action is archive:
            self.archive_requested.emit(self._project_id())
        elif action is delete:
            self.delete_requested.emit(self._project_id())
