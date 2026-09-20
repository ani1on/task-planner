from PySide6.QtWidgets import QLabel, QVBoxLayout

from .base_page import BasePage


class NotesPage(BasePage):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)

        title = QLabel("Notes")
        title.setObjectName("pageTitle")

        layout.addWidget(title)
        layout.addStretch()
