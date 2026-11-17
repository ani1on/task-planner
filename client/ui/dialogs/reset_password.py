from PySide6.QtWidgets import QHBoxLayout

from client.ui.components import (
    FormField,
    PasswordInput,
    PrimaryButton,
    SecondaryButton,
    TextInput,
)

from .base import BaseDialog


class ResetPasswordDialog(BaseDialog):
    """Ввод токена из письма и нового пароля."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Сброс пароля")
        self.setMinimumWidth(420)
        self.layout.setContentsMargins(24, 22, 24, 20)
        self.layout.setSpacing(12)

        self.token = TextInput("Код из письма")
        self.password = PasswordInput("Новый пароль")
        self.confirm = PasswordInput("Повторите пароль")
        self.token_field = FormField("Код восстановления", self.token)
        self.password_field = FormField("Новый пароль", self.password)
        self.confirm_field = FormField("Повторите пароль", self.confirm)
        self.layout.addWidget(self.token_field)
        self.layout.addWidget(self.password_field)
        self.layout.addWidget(self.confirm_field)

        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel = SecondaryButton("Отмена")
        cancel.clicked.connect(self.reject)
        submit = PrimaryButton("Сменить пароль")
        submit.clicked.connect(self.accept)
        buttons.addWidget(cancel)
        buttons.addWidget(submit)
        self.layout.addLayout(buttons)

    def accept(self):
        self.token_field.clear_error()
        self.password_field.clear_error()
        self.confirm_field.clear_error()
        valid = True
        if not self.token.text().strip():
            self.token_field.set_error("Введите код из письма")
            valid = False
        if len(self.password.text()) < 8:
            self.password_field.set_error("Минимум 8 символов")
            valid = False
        if self.password.text() != self.confirm.text():
            self.confirm_field.set_error("Пароли не совпадают")
            valid = False
        if valid:
            super().accept()

    def values(self) -> tuple[str, str]:
        return self.token.text().strip(), self.password.text()
