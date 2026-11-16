from PySide6.QtWidgets import QProgressBar


class ProgressBar(QProgressBar):
    def __init__(
        self,
        value: int = 0,
        parent=None,
    ):
        super().__init__(parent)

        self.setRange(0, 100)
        self.setValue(value)
        self.setTextVisible(False)
        self.setProperty("component", "progress")
