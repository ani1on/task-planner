from PySide6.QtWidgets import QLabel


class SectionTitle(QLabel):
    """Заголовок блока внутри страницы."""

    def __init__(
        self,
        text: str,
        parent=None,
    ):
        super().__init__(text, parent)

        self.setProperty("role", "section-title")
