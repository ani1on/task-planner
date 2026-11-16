import sys

from PySide6.QtWidgets import QApplication

from client.api.client import ApiClient
from client.core.config import Config
from client.services.auth import AuthService
from client.themes import ThemeManager
from client.ui.app_window import AppWindow


def main():
    app = QApplication(sys.argv)

    # API
    api = ApiClient(
        base_url=Config.API_URL,
        timeout=Config.API_TIMEOUT,
    )

    # Auth
    auth_service = AuthService(api)

    # Themes
    theme_manager = ThemeManager(app)
    theme_manager.set_theme("light")

    # Application window
    window = AppWindow(
        api=api,
        auth_service=auth_service,
        theme_manager=theme_manager,
    )

    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
