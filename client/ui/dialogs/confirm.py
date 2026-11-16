from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton

from .base import BaseDialog


class ConfirmDialog(BaseDialog):
    def __init__(
        self,
        message: str,
        parent=None,
    ):
        super().__init__(parent)

        self.setWindowTitle("Подтверждение")

        message_label = QLabel(message)

        self.layout.addWidget(message_label)

        buttons_layout = QHBoxLayout()

        yes_button = QPushButton("Да")
        no_button = QPushButton("Нет")

        yes_button.clicked.connect(self.accept)
        no_button.clicked.connect(self.reject)

        buttons_layout.addWidget(yes_button)
        buttons_layout.addWidget(no_button)

        self.layout.addLayout(buttons_layout)
