from PySide6.QtCore import QSize
from PySide6.QtWidgets import QPushButton

from client.ui.icons import make_icon


class PrimaryButton(QPushButton):
    def __init__(
        self,
        text: str,
        icon_name: str | None = None,
        parent=None,
    ):
        super().__init__(text, parent)

        self.setProperty(
            "variant",
            "primary",
        )

        if icon_name:
            self.setIcon(make_icon(icon_name, color="#ffffff"))
            self.setIconSize(QSize(16, 16))


class SecondaryButton(QPushButton):
    def __init__(
        self,
        text: str,
        icon_name: str | None = None,
        parent=None,
    ):
        super().__init__(text, parent)

        self.setProperty(
            "variant",
            "secondary",
        )

        if icon_name:
            self.setIcon(make_icon(icon_name))
            self.setIconSize(QSize(16, 16))


class DangerButton(QPushButton):
    def __init__(
        self,
        text: str,
        parent=None,
    ):
        super().__init__(text, parent)

        self.setProperty(
            "variant",
            "danger",
        )
