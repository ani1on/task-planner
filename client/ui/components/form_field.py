from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class FormField(QWidget):
    """Поле формы: подпись, ввод, подсказка и текст ошибки."""

    def __init__(
        self,
        label: str,
        field,
        hint: str = "",
        parent=None,
    ):
        super().__init__(parent)

        self.field = field

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.label = QLabel(label)
        self.label.setProperty("role", "form-label")

        layout.addWidget(self.label)
        layout.addWidget(self.field)

        self.hint = None
        if hint:
            self.hint = QLabel(hint)
            self.hint.setProperty("role", "form-hint")
            layout.addWidget(self.hint)

        self.error = QLabel()
        self.error.setProperty("role", "form-error")
        self.error.setWordWrap(True)
        self.error.hide()

        layout.addWidget(self.error)

        self.field.textChanged.connect(self.clear_error)

    def value(self) -> str:
        return self.field.text()

    def set_error(self, message: str):
        if not message:
            self.clear_error()
            return

        self.error.setText(message)
        self.error.show()

        if self.hint is not None:
            self.hint.hide()

        self._set_invalid(True)

    def clear_error(self):
        if not self.error.isVisible():
            return

        self.error.clear()
        self.error.hide()

        if self.hint is not None:
            self.hint.show()

        self._set_invalid(False)

    def _set_invalid(self, invalid: bool):
        self.field.setProperty("invalid", "true" if invalid else "false")
        self.field.style().unpolish(self.field)
        self.field.style().polish(self.field)
