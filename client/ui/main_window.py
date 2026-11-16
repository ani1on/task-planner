import contextlib

from PySide6.QtWidgets import (
    QHBoxLayout,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from client.api.client import ApiClient
from client.services.auth import AuthService
from client.themes import ThemeManager
from client.ui.components import Header, Sidebar
from client.ui.pages import (
    CalendarPage,
    DashboardPage,
    KanbanPage,
    NotesPage,
    ProjectsPage,
    SettingsPage,
    TasksPage,
)


class MainWindow(QWidget):
    """Основной экран приложения: навигация, шапка и стек страниц."""

    def __init__(
        self,
        api: ApiClient,
        auth_service: AuthService,
        theme_manager: ThemeManager,
        on_logout=None,
        demo: bool = False,
        parent=None,
    ):
        super().__init__(parent)

        self.api = api
        self.auth_service = auth_service
        self.theme_manager = theme_manager
        self.on_logout = on_logout
        self.demo = demo

        self.setObjectName("MainWindow")

        self._build_ui()

    def _build_ui(self):
        user = self.auth_service.user

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.sidebar = Sidebar(user)
        self.sidebar.navigate.connect(self.navigate_to)
        self.sidebar.theme_toggled.connect(self.toggle_theme)
        self.sidebar.logout_requested.connect(self.logout)
        self.sidebar.set_theme(self.theme_manager.current_theme)

        root.addWidget(self.sidebar)

        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(0)

        self.header = Header(user)

        self.stack = QStackedWidget()

        # В demo-режиме api=None — страницы берут данные из mock_data.
        page_api = None if self.demo else self.api

        self.pages = {
            "dashboard": DashboardPage(api=page_api, demo=self.demo),
            "tasks": TasksPage(api=page_api, demo=self.demo),
            "kanban": KanbanPage(api=page_api, demo=self.demo),
            "projects": ProjectsPage(api=page_api, demo=self.demo),
            "calendar": CalendarPage(api=page_api, demo=self.demo),
            "notes": NotesPage(api=page_api, demo=self.demo),
            "settings": SettingsPage(user, self.auth_service),
        }

        settings = self.pages["settings"]
        settings.theme_toggled.connect(self.toggle_theme)
        settings.logout_requested.connect(self.logout)

        for page in self.pages.values():
            self.stack.addWidget(page)

        right.addWidget(self.header)
        right.addWidget(self.stack, 1)

        root.addLayout(right, 1)

        self.navigate_to("dashboard")

    def navigate_to(self, key: str):
        page = self.pages.get(key)
        if page is None:
            return

        self.stack.setCurrentWidget(page)
        self.sidebar.set_active(key)

        if key == "settings":
            page.refresh_settings()
        else:
            page.reload()

    def refresh_user(self):
        user = self.auth_service.user

        self.sidebar.set_user(user)
        self.header.set_user(user)
        self.pages["settings"].set_user(user)

    def toggle_theme(self):
        self.theme_manager.toggle()
        self.sidebar.set_theme(self.theme_manager.current_theme)

        with contextlib.suppress(Exception):
            self.auth_service.update_settings(
                theme=self.theme_manager.current_theme,
            )

    def logout(self):
        try:
            self.auth_service.logout()
        except Exception:
            self.auth_service.clear_auth()

        if self.on_logout:
            self.on_logout()

