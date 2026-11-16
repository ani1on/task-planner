from PySide6.QtWidgets import QHBoxLayout

from client.ui.components import (
    FormField,
    PrimaryButton,
    SecondaryButton,
    TextInput,
)

from .base import BaseDialog


class ProfileDialog(BaseDialog):
    """Диалог редактирования никнейма и аватара."""

    def __init__(
        self,
        user: dict | None = None,
        parent=None,
    ):
        super().__init__(parent)

        self.setWindowTitle("Редактирование профиля")

        user = user or {}

        self.nick_name_field = FormField(
            "Никнейм",
            TextInput("Ваш никнейм"),
        )
        self.nick_name_field.field.setText(user.get("nick_name") or "")

        self.avatar_field = FormField(
            "Ссылка на аватар",
            TextInput("https://..."),
            hint="Необязательно",
        )
        self.avatar_field.field.setText(user.get("avatar_url") or "")

        self.layout.addWidget(self.nick_name_field)
        self.layout.addWidget(self.avatar_field)

        buttons = QHBoxLayout()

        cancel = SecondaryButton("Отмена")
        cancel.clicked.connect(self.reject)

        save = PrimaryButton("Сохранить")
        save.clicked.connect(self.accept)

        buttons.addStretch()
        buttons.addWidget(cancel)
        buttons.addWidget(save)

        self.layout.addLayout(buttons)

        self.nick_name_field.field.setFocus()

    def values(self) -> dict:
        data = {"nick_name": self.nick_name_field.value().strip()}

        avatar_url = self.avatar_field.value().strip()

        if avatar_url:
            data["avatar_url"] = avatar_url

        return data
