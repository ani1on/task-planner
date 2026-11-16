from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel


class Badge(QLabel):
    """Небольшая цветная метка для статусов, приоритетов и тегов."""

    def __init__(
        self,
        text: str = "",
        variant: str = "neutral",
        parent=None,
    ):
        super().__init__(text, parent)

        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setProperty("badge", variant)

    def set_variant(self, variant: str):
        self.setProperty("badge", variant)
        self.style().unpolish(self)
        self.style().polish(self)
