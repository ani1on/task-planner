from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class EmptyState(QWidget):
    def __init__(
        self,
        message: str = "Здесь пока ничего нет",
        parent=None,
    ):
        super().__init__(parent)

        layout = QVBoxLayout(self)

        label = QLabel(message)

        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(label)
