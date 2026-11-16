from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from client.ui.icons import make_icon

from .avatar import Avatar
from .nav_button import NavButton

NAV_ITEMS = [
    ("dashboard", "Дашборд", "grid"),
    ("tasks", "Задачи", "list"),
    ("kanban", "Канбан", "columns"),
    ("projects", "Проекты", "folder"),
    ("calendar", "Календарь", "calendar"),
    ("notes", "Заметки", "note"),
    ("settings", "Настройки", "sliders"),
]


class Sidebar(QFrame):
    """Боковая панель: логотип, навигация, тема и профиль."""

    navigate = Signal(str)
    theme_toggled = Signal()
    logout_requested = Signal()

    def __init__(self, user: dict | None = None, parent=None):
        super().__init__(parent)

        self.setObjectName("Sidebar")
        self.setFixedWidth(244)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 20, 16, 16)
        layout.setSpacing(6)

        layout.addLayout(self._build_logo())
        layout.addSpacing(14)

        self.group = QButtonGroup(self)
        self.group.setExclusive(True)

        self.buttons: dict[str, NavButton] = {}

        for key, label, icon_name in NAV_ITEMS:
            button = NavButton(label, icon_name)
            button.clicked.connect(
                lambda _checked=False, name=key: self.navigate.emit(name)
            )

            self.group.addButton(button)
            self.buttons[key] = button

            layout.addWidget(button)

        layout.addStretch()

        self.theme_button = QPushButton("Тёмная тема")
        self.theme_button.setIcon(make_icon("moon"))
        self.theme_button.setIconSize(QSize(18, 18))
        self.theme_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_button.setProperty("nav", "true")
        self.theme_button.clicked.connect(self.theme_toggled.emit)

        layout.addWidget(self.theme_button)

        separator = QFrame()
        separator.setObjectName("SidebarSeparator")
        separator.setFixedHeight(1)
        layout.addWidget(separator)

        layout.addLayout(self._build_profile(user))

    def _build_logo(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(10)

        mark = QLabel("TP")
        mark.setObjectName("LogoMark")
        mark.setFixedSize(34, 34)
        mark.setAlignment(Qt.AlignmentFlag.AlignCenter)

        name = QLabel("Task Planner")
        name.setObjectName("Logo")

        layout.addWidget(mark)
        layout.addWidget(name)
        layout.addStretch()

        return layout

    def _build_profile(self, user: dict | None) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(10)

        self.avatar = Avatar("", size=36)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(1)

        self.profile_name = QLabel()
        self.profile_name.setObjectName("ProfileName")

        self.profile_email = QLabel()
        self.profile_email.setProperty("role", "muted")

        text_layout.addWidget(self.profile_name)
        text_layout.addWidget(self.profile_email)

        self.logout_button = QPushButton()
        self.logout_button.setIcon(make_icon("logout"))
        self.logout_button.setIconSize(QSize(18, 18))
        self.logout_button.setToolTip("Выйти из аккаунта")
        self.logout_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.logout_button.setProperty("icon", "true")
        self.logout_button.clicked.connect(self.logout_requested.emit)

        layout.addWidget(self.avatar)
        layout.addLayout(text_layout, 1)
        layout.addWidget(self.logout_button)

        self.set_user(user)

        return layout

    def set_user(self, user: dict | None):
        user = user or {}

        name = user.get("nick_name") or "Гость"
        email = user.get("email") or "Нет данных"

        self.avatar.set_name(name)
        self.profile_name.setText(name)
        self.profile_email.setText(email)

    def set_active(self, key: str):
        button = self.buttons.get(key)
        if button is not None:
            button.setChecked(True)

    def set_theme(self, theme: str):
        if theme == "dark":
            self.theme_button.setText("Светлая тема")
            self.theme_button.setIcon(make_icon("sun"))
        else:
            self.theme_button.setText("Тёмная тема")
            self.theme_button.setIcon(make_icon("moon"))
