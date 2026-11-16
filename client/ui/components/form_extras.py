from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

VARIANTS = {
    "error": "form-error-banner",
    "success": "form-success-banner",
}


class FormError(QLabel):
    """Общее сообщение формы: ошибка отправки или результат действия."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setProperty("role", VARIANTS["error"])
        self.setWordWrap(True)
        self.hide()

    def show_message(self, message: str, variant: str = "error"):
        self.setProperty("role", VARIANTS.get(variant, VARIANTS["error"]))

        self.style().unpolish(self)
        self.style().polish(self)

        self.setText(message)
        self.show()

    def clear_message(self):
        self.clear()
        self.hide()


class LinkButton(QPushButton):
    """Кнопка, оформленная как текстовая ссылка."""

    def __init__(
        self,
        text: str,
        on_click=None,
        parent=None,
    ):
        super().__init__(text, parent)

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setProperty("link", "true")

        if on_click is not None:
            self.clicked.connect(on_click)


class LinkRow(QWidget):
    """Строка вида «Текст» + кнопка-ссылка."""

    def __init__(
        self,
        text: str,
        link_text: str,
        on_click=None,
        parent=None,
    ):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        label = QLabel(text)
        label.setProperty("role", "muted")

        self.link = LinkButton(link_text, on_click)

        layout.addStretch()
        layout.addWidget(label)
        layout.addWidget(self.link)
        layout.addStretch()
