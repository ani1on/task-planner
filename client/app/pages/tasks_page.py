from PySide6.QtWidgets import QLabel, QVBoxLayout

from .base_page import BasePage


class TasksPage(BasePage):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)

        title = QLabel("Tasks")
        title.setObjectName("pageTitle")

        layout.addWidget(title)
        layout.addStretch()
