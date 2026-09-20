from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class Sidebar(QWidget):
    page_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("sidebar")
        self.setFixedWidth(220)

        self._buttons = QButtonGroup(self)
        self._buttons.setExclusive(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(6)

        # Dashboard
        self.dashboard_button = self._create_button(
            "Dashboard",
            "dashboard",
        )
        layout.addWidget(self.dashboard_button)

        # Tasks
        self.tasks_button = self._create_button(
            "Tasks",
            "tasks",
        )
        layout.addWidget(self.tasks_button)

        # Projects
        self.projects_button = self._create_button(
            "Projects",
            "projects",
        )
        layout.addWidget(self.projects_button)

        # Calendar
        self.calendar_button = self._create_button("Calendar", "calendar")
        layout.addWidget(self.calendar_button)

        # Notes
        self.notes_button = self._create_button("Notes", "notes")
        layout.addWidget(self.notes_button)

        # Свободное пространство
        layout.addStretch()

        # Settings
        self.settings_button = self._create_button(
            "Settings",
            "settings",
        )
        layout.addWidget(self.settings_button)

        # Dashboard выбран по умолчанию
        self.dashboard_button.setChecked(True)

    def _create_button(
        self,
        text: str,
        page_name: str,
    ) -> QPushButton:
        button = QPushButton(text)

        button.setCheckable(True)
        button.setObjectName("sidebarButton")

        button.clicked.connect(lambda: self.page_changed.emit(page_name))

        self._buttons.addButton(button)

        return button
