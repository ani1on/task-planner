from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel


class LoadingWidget(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setText("Загрузка...")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.hide()

    def start(self):
        self.show()

    def stop(self):
        self.hide()
