from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QToolButton,
    QVBoxLayout,
)

from client.core.constants import (
    PROJECT_COLOR_LABELS,
    PROJECT_COLORS,
    PROJECT_STATUS_ACTIVE,
    PROJECT_STATUS_LABELS,
)

from .avatar import Avatar
from .badge import Badge
from .progress_bar import ProgressBar


class ProjectCard(QFrame):
    """Карточка проекта с прогрессом и участниками."""

    save_requested = Signal(int, dict)
    delete_requested = Signal(int)
    members_requested = Signal(int)

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
        self.color_dot = dot

        name = QLabel(project.get("name", ""))
        name.setProperty("role", "card-title")
        self.name_label = name

        self.more_button = QToolButton()
        self.more_button.setText("⋯")
        self.more_button.setToolTip("Изменить проект и дополнительные действия")
        self.more_button.setProperty("icon", "true")
        self.more_button.clicked.connect(self.toggle_details)

        header.addWidget(dot)
        header.addWidget(name)
        header.addStretch()
        header.addWidget(self.more_button)

        status = project.get("status", "active")
        self.status_badge = Badge(
            PROJECT_STATUS_LABELS.get(status, status),
            "success" if status == "active" else "neutral",
        )
        header.addWidget(self.status_badge)

        description = QLabel(project.get("description", ""))
        description.setProperty("role", "muted")
        description.setWordWrap(True)
        self.description_label = description

        done = project.get("done", 0)
        total = project.get("total", 0)
        percent = int(done / total * 100) if total else 0

        progress = ProgressBar(percent)
        self.progress = progress

        progress_label = QLabel(f"{done} из {total} задач")
        progress_label.setProperty("role", "muted")
        self.progress_label = progress_label

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

        self.details = QFrame()
        self.details.setProperty("component", "card")
        details_layout = QVBoxLayout(self.details)
        details_layout.setContentsMargins(12, 12, 12, 12)
        details_layout.setSpacing(8)

        self.name_input = QLineEdit(project.get("name", ""))
        self.name_error = QLabel()
        self.name_error.setProperty("role", "form-error")
        self.name_error.hide()
        self.description_input = QPlainTextEdit(project.get("description", ""))
        self.description_input.setPlaceholderText("Описание проекта")
        self.description_input.setFixedHeight(72)
        self.color_combo = QComboBox()
        for key, label in PROJECT_COLOR_LABELS.items():
            self.color_combo.addItem(label, key)
        self._select(self.color_combo, project.get("color", "blue"))
        self.status_combo = QComboBox()
        for key, label in PROJECT_STATUS_LABELS.items():
            self.status_combo.addItem(label, key)
        self._select(self.status_combo, project.get("status", PROJECT_STATUS_ACTIVE))

        details_layout.addWidget(QLabel("Название"))
        details_layout.addWidget(self.name_input)
        details_layout.addWidget(self.name_error)
        details_layout.addWidget(QLabel("Описание"))
        details_layout.addWidget(self.description_input)
        fields = QHBoxLayout()
        fields.addWidget(self.color_combo)
        fields.addWidget(self.status_combo)
        details_layout.addLayout(fields)

        actions = QHBoxLayout()
        save = QPushButton("Сохранить")
        save.clicked.connect(self.save)
        members_button = QPushButton("Участники")
        members_button.clicked.connect(
            lambda: self.members_requested.emit(self._project_id())
        )
        delete = QPushButton("Удалить")
        delete.clicked.connect(
            lambda: self.delete_requested.emit(self._project_id())
        )
        actions.addWidget(save)
        actions.addWidget(members_button)
        actions.addWidget(delete)
        details_layout.addLayout(actions)
        self.details_layout = details_layout
        self.details.hide()
        layout.addWidget(self.details)
        self.members_panel = None

    @staticmethod
    def _select(combo: QComboBox, value):
        index = combo.findData(value)
        if index >= 0:
            combo.setCurrentIndex(index)

    def toggle_details(self):
        visible = self.details.isHidden()
        self.details.setVisible(visible)
        if not visible and self.members_panel is not None:
            self.members_panel.hide()

    def save(self):
        name = self.name_input.text().strip()
        if not name:
            self.name_error.setText("Введите название проекта")
            self.name_error.show()
            self.name_input.setFocus()
            return
        self.name_error.hide()
        self.save_requested.emit(
            self._project_id(),
            {
                "name": name,
                "description": self.description_input.toPlainText().strip() or None,
                "color": self.color_combo.currentData(),
                "status": self.status_combo.currentData(),
            },
        )

    def set_members_panel(self, panel):
        if self.members_panel is not None:
            self.details_layout.removeWidget(self.members_panel)
            self.members_panel.deleteLater()
        self.members_panel = panel
        if panel is not None:
            self.details_layout.addWidget(panel)
            self.details.show()
            panel.show()

    def update_project(self, project: dict):
        self.project.update(project)
        self.name_label.setText(project.get("name", ""))
        self.description_label.setText(project.get("description") or "")
        self.name_input.setText(project.get("name", ""))
        self.description_input.setPlainText(project.get("description") or "")
        self._select(self.color_combo, project.get("color", "blue"))
        self._select(self.status_combo, project.get("status", "active"))
        color = PROJECT_COLORS.get(project.get("color"), PROJECT_COLORS["blue"])
        self.color_dot.setStyleSheet(
            f"background-color: {color}; border-radius: 5px;"
        )
        self.status_badge.setText(
            PROJECT_STATUS_LABELS.get(project.get("status"), project.get("status", ""))
        )
        self.status_badge.set_variant(
            "success" if project.get("status") == "active" else "neutral"
        )
    def _project_id(self) -> int:
        return int(self.project.get("id") or 0)
