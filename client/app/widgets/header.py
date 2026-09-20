from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QWidget,
)


class Header(QWidget):
    PAGE_TITLES = {
        "dashboard": "Dashboard",
        "tasks": "Tasks",
        "projects": "Projects",
        "calendar": "Calendar",
        "settings": "Settings",
        "notes": "Notes",
    }

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("header")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(
            24,
            16,
            24,
            16,
        )

        self.title = QLabel("Dashboard")
        self.title.setObjectName("headerTitle")

        layout.addWidget(self.title)
        layout.addStretch()

    def set_title(self, page_name: str):
        title = self.PAGE_TITLES.get(
            page_name,
            page_name.capitalize(),
        )

        self.title.setText(title)
