from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QMenu,
    QPushButton,
)

from client.ui.icons import make_icon

from .avatar import Avatar
from .badge import Badge


class Header(QFrame):
    """Верхняя панель: уведомления и профиль."""

    notifications_requested = Signal()
    profile_requested = Signal()
    logout_requested = Signal()

    def __init__(self, user: dict | None = None, parent=None):
        super().__init__(parent)

        self.setObjectName("Header")
        self.setFixedHeight(64)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 0, 24, 0)
        layout.setSpacing(12)

        notifications = QPushButton()
        notifications.setIcon(make_icon("bell"))
        notifications.setIconSize(QSize(20, 20))
        notifications.setToolTip("Уведомления")
        notifications.setCursor(Qt.CursorShape.PointingHandCursor)
        notifications.setProperty("icon", "true")
        notifications.clicked.connect(self.notifications_requested.emit)

        self.notifications_button = notifications

        self.unread_badge = Badge("0", "danger")
        self.unread_badge.hide()

        self.avatar = Avatar("", size=36)
        self.avatar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.avatar.mousePressEvent = lambda event: self._show_avatar_menu()

        self.avatar_menu = QMenu(self)

        layout.addStretch()
        layout.addWidget(notifications)
        layout.addWidget(self.unread_badge)
        layout.addWidget(self.avatar)

        self.set_user(user)

    def set_user(self, user: dict | None):
        user = user or {}
        self.avatar.set_name(user.get("nick_name") or "Гость")
        self._user = user

        self.avatar_menu.clear()
        name = user.get("nick_name") or "Гость"
        email = user.get("email") or ""

        info = self.avatar_menu.addAction(f"{name}\n{email}".strip())
        info.setEnabled(False)
        self.avatar_menu.addSeparator()

        settings_action = self.avatar_menu.addAction("Настройки")
        settings_action.triggered.connect(self.profile_requested.emit)

        logout_action = self.avatar_menu.addAction("Выйти")
        logout_action.triggered.connect(self.logout_requested.emit)

    def _show_avatar_menu(self):
        self.avatar_menu.exec(self.avatar.mapToGlobal(self.avatar.rect().bottomLeft()))

    def set_unread_count(self, count: int):
        count = max(0, int(count or 0))
        self.unread_badge.setText(str(count))
        self.unread_badge.setVisible(count > 0)
