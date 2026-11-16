from PySide6.QtWidgets import QDialog, QVBoxLayout


class BaseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout(self)

        self.setModal(True)
