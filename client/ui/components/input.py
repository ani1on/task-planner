from PySide6.QtWidgets import QLineEdit

from client.ui.icons import make_icon


class TextInput(QLineEdit):
    def __init__(
        self,
        placeholder: str = "",
        parent=None,
    ):
        super().__init__(parent)

        self.setPlaceholderText(placeholder)


class PasswordInput(QLineEdit):
    def __init__(
        self,
        placeholder: str = "Пароль",
        parent=None,
    ):
        super().__init__(parent)

        self.setPlaceholderText(placeholder)

        self.setEchoMode(QLineEdit.EchoMode.Password)

        self._visible = False

        self._toggle_action = self.addAction(
            make_icon("eye"),
            QLineEdit.ActionPosition.TrailingPosition,
        )
        self._toggle_action.setToolTip("Показать пароль")
        self._toggle_action.triggered.connect(self.toggle_visibility)

    def toggle_visibility(self):
        self._visible = not self._visible

        self.setEchoMode(
            QLineEdit.EchoMode.Normal if self._visible else QLineEdit.EchoMode.Password
        )

        self._toggle_action.setIcon(make_icon("eye_off" if self._visible else "eye"))
        self._toggle_action.setToolTip(
            "Скрыть пароль" if self._visible else "Показать пароль"
        )
