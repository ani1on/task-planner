from PySide6.QtWidgets import QMainWindow, QStackedWidget

from client.api.client import ApiClient
from client.services.auth import AuthService
from client.themes import ThemeManager
from client.ui.main_window import MainWindow
from client.ui.mock_data import current_user
from client.ui.pages import LoginPage, RegisterPage


class AppWindow(QMainWindow):
    def __init__(
        self,
        api: ApiClient,
        auth_service: AuthService,
        theme_manager: ThemeManager,
    ):
        super().__init__()

        self.api = api
        self.auth_service = auth_service
        self.theme_manager = theme_manager

        self.setWindowTitle("Task Planner")
        self.resize(1240, 800)
        self.setMinimumSize(1024, 680)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.login_page = LoginPage(
            auth_service=self.auth_service,
            on_login=self.show_main_window,
            on_register=self.show_register_page,
            on_demo=self.show_demo,
        )

        self.register_page = RegisterPage(
            auth_service=self.auth_service,
            on_registered=self.show_login_page,
            on_login=self.show_login_page,
        )

        self.main_window = MainWindow(
            api=self.api,
            auth_service=self.auth_service,
            theme_manager=self.theme_manager,
            on_logout=self.show_login_page,
            demo=False,
        )

        self.stack.addWidget(self.login_page)
        self.stack.addWidget(self.register_page)
        self.stack.addWidget(self.main_window)

        self.show_login_page()

    def show_login_page(self):
        self.stack.setCurrentWidget(self.login_page)

    def show_register_page(self):
        self.stack.setCurrentWidget(self.register_page)

    def show_main_window(self, user=None):
        self.main_window.refresh_user()
        self._apply_saved_theme()
        self.stack.setCurrentWidget(self.main_window)

    def _apply_saved_theme(self):
        try:
            settings = self.auth_service.get_settings()
        except Exception:
            return

        theme = settings.get("theme")

        if theme:
            self.theme_manager.set_theme(theme)
            self.main_window.sidebar.set_theme(theme)

    def show_demo(self):
        """Открывает каркас с моковым пользователем, без обращения к API."""
        self.auth_service.user = current_user()
        self.show_main_window(self.auth_service.user)
