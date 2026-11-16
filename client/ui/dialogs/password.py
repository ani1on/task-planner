from PySide6.QtWidgets import QHBoxLayout

from client.ui.components import (
    FormField,
    PasswordInput,
    PrimaryButton,
    SecondaryButton,
)

from .base import BaseDialog


class PasswordDialog(BaseDialog):
    """Диалог смены пароля."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Смена пароля")

        self.current_field = FormField(
            "Текущий пароль",
            PasswordInput("Текущий пароль"),
        )
        self.new_field = FormField(
            "Новый пароль",
            PasswordInput("Минимум 8 символов"),
            hint="Минимум 8 символов",
        )

        self.layout.addWidget(self.current_field)
        self.layout.addWidget(self.new_field)

        buttons = QHBoxLayout()

        cancel = SecondaryButton("Отмена")
        cancel.clicked.connect(self.reject)

        save = PrimaryButton("Сменить пароль")
        save.clicked.connect(self.accept)

        buttons.addStretch()
        buttons.addWidget(cancel)
        buttons.addWidget(save)

        self.layout.addLayout(buttons)

        self.current_field.field.setFocus()

    def values(self) -> tuple[str, str]:
        return (
            self.current_field.value(),
            self.new_field.value(),
        )
