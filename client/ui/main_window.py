import contextlib

from PySide6.QtWidgets import QHBoxLayout, QStackedWidget, QVBoxLayout, QWidget

from client.api.client import ApiClient
from client.core.realtime import RealtimeClient
from client.services.auth import AuthService
from client.services.notifications import NotificationService
from client.themes import ThemeManager
from client.ui.components import Header, Sidebar
from client.ui.dialogs.notifications import NotificationsPanel
from client.ui.error_handler import error_message
from client.ui.pages import (
    ActivityPage,
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
        parent=None,
    ):
        super().__init__(parent)

        self.api = api
        self.auth_service = auth_service
        self.theme_manager = theme_manager
        self.on_logout = on_logout
        self.realtime = None

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
        self.header.notifications_requested.connect(self.open_notifications)
        self.header.profile_requested.connect(lambda: self.navigate_to("settings"))
        self.header.logout_requested.connect(self.logout)

        self.stack = QStackedWidget()
        self.notifications_panel = NotificationsPanel(self.api, self)
        self.notifications_panel.changed.connect(self.refresh_notifications)

        user_id = (self.auth_service.user or {}).get("id")
        self.pages = {
            "dashboard": DashboardPage(api=self.api, user_id=user_id),
            "tasks": TasksPage(api=self.api, user_id=user_id),
            "kanban": KanbanPage(api=self.api, user_id=user_id),
            "projects": ProjectsPage(api=self.api, user_id=user_id),
            "calendar": CalendarPage(api=self.api),
            "activity": ActivityPage(api=self.api),
            "notes": NotesPage(api=self.api),
            "settings": SettingsPage(user, self.auth_service),
        }

        settings = self.pages["settings"]
        settings.theme_toggled.connect(self.toggle_theme)
        settings.logout_requested.connect(self.logout)

        for page in self.pages.values():
            self.stack.addWidget(page)

        right.addWidget(self.header)
        right.addWidget(self.notifications_panel)
        self.notifications_panel.hide()
        right.addWidget(self.stack, 1)

        root.addLayout(right, 1)

        self.navigate_to("dashboard")

    # ==================================================================
    # Уведомления
    # ==================================================================

    def open_notifications(self):
        self.notifications_panel.setVisible(self.notifications_panel.isHidden())
        if self.notifications_panel.isVisible():
            self.notifications_panel.reload()

    # ==================================================================
    # Вспомогательные методы
    # ==================================================================

    def refresh_notifications(self):
        try:
            count = NotificationService(self.api).unread_count()
        except Exception as error:
            self.header.unread_badge.setToolTip(
                f"Не удалось загрузить уведомления: {error_message(error)}"
            )
            return

        self.header.set_unread_count(count)
        self.header.unread_badge.setToolTip("")
        if self.notifications_panel.isVisible():
            self.notifications_panel.reload()

    def on_realtime_event(self, event: dict):
        event_type = event.get("type") or event.get("event") or event.get("action")
        if event_type == "notification_created":
            self.refresh_notifications()
        # Инвалидация текущей страницы по событиям задач.
        page = self.stack.currentWidget()
        if hasattr(page, "reload"):
            page.reload()

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

        user_id = (user or {}).get("id")

        for key in ("dashboard", "tasks", "kanban", "projects"):
            page = self.pages.get(key)
            if page is not None and hasattr(page, "user_id"):
                page.user_id = user_id

        self.refresh_notifications()

        if self.auth_service.access_token and self.realtime is None:
            self.realtime = RealtimeClient(
                self.api.base_url,
                self.auth_service.access_token,
                self,
            )
            self.realtime.event_received.connect(self.on_realtime_event)
            self.realtime.connect()

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
