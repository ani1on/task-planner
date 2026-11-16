from PySide6.QtWidgets import QLabel, QPushButton

from .base import BaseDialog


class ErrorDialog(BaseDialog):
    def __init__(
        self,
        message: str,
        parent=None,
    ):
        super().__init__(parent)

        self.setWindowTitle("Ошибка")

        message_label = QLabel(message)

        self.layout.addWidget(message_label)

        button = QPushButton("OK")

        button.clicked.connect(self.accept)

        self.layout.addWidget(button)
