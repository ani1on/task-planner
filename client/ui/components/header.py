from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
)

from client.ui.icons import make_icon

from .avatar import Avatar
from .badge import Badge


class Header(QFrame):
    """Верхняя панель: поиск, уведомления и профиль."""

    search_changed = Signal(str)
    notifications_requested = Signal()

    def __init__(self, user: dict | None = None, parent=None):
        super().__init__(parent)

        self.setObjectName("Header")
        self.setFixedHeight(64)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 0, 24, 0)
        layout.setSpacing(12)

        self.search = QLineEdit()
        self.search.setObjectName("SearchInput")
        self.search.setPlaceholderText("Поиск по задачам, проектам и заметкам")
        self.search.setFixedWidth(340)
        self.search.addAction(
            make_icon("search"),
            QLineEdit.ActionPosition.LeadingPosition,
        )
        self.search.textChanged.connect(self.search_changed.emit)

        notifications = QPushButton()
        notifications.setIcon(make_icon("bell"))
        notifications.setIconSize(QSize(20, 20))
        notifications.setToolTip("Уведомления")
        notifications.setCursor(Qt.CursorShape.PointingHandCursor)
        notifications.setProperty("icon", "true")
        notifications.clicked.connect(self.notifications_requested.emit)

        unread = Badge("2", "danger")

        self.avatar = Avatar("", size=36)

        layout.addWidget(self.search)
        layout.addStretch()
        layout.addWidget(notifications)
        layout.addWidget(unread)
        layout.addWidget(self.avatar)

        self.set_user(user)

    def set_user(self, user: dict | None):
        user = user or {}
        self.avatar.set_name(user.get("nick_name") or "Гость")
