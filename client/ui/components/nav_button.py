from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QPushButton

from client.ui.icons import make_icon


class NavButton(QPushButton):
    """Пункт боковой навигации."""

    def __init__(
        self,
        text: str,
        icon_name: str | None = None,
        parent=None,
    ):
        super().__init__(text, parent)

        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setProperty("nav", "true")

        if icon_name:
            self.setIcon(make_icon(icon_name))
            self.setIconSize(QSize(18, 18))
