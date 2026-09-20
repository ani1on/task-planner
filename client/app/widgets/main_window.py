from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from client.app.navigation import NavigationManager
from client.app.pages import (
    CalendarPage,
    DashboardPage,
    NotesPage,
    ProjectsPage,
    SettingsPage,
    TasksPage,
)

from .header import Header
from .sidebar import Sidebar


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Task Planner")
        self.resize(1200, 700)

        self._setup_ui()
        self._setup_navigation()
        self._connect_signals()

    def _setup_ui(self):
        central_widget = QWidget()
        central_widget.setObjectName("centralWidget")

        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        self.sidebar = Sidebar()

        # Content
        content_widget = QWidget()

        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Header
        self.header = Header()

        # Page container
        self.pages = QStackedWidget()

        content_layout.addWidget(self.header)
        content_layout.addWidget(self.pages)

        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(content_widget)

    def _setup_navigation(self):
        self.navigation = NavigationManager(self.pages)

        self.dashboard_page = DashboardPage()
        self.tasks_page = TasksPage()
        self.projects_page = ProjectsPage()
        self.settings_page = SettingsPage()
        self.calendar_page = CalendarPage()
        self.notes_page = NotesPage()

        self.navigation.register_page(
            "dashboard",
            self.dashboard_page,
        )

        self.navigation.register_page(
            "tasks",
            self.tasks_page,
        )

        self.navigation.register_page(
            "projects",
            self.projects_page,
        )

        self.navigation.register_page(
            "settings",
            self.settings_page,
        )

        self.navigation.register_page("calendar", self.calendar_page)

        self.navigation.register_page("notes", self.notes_page)

        # Страница по умолчанию
        self.navigation.navigate("dashboard")

    def _connect_signals(self):
        self.sidebar.page_changed.connect(self.navigation.navigate)

        self.navigation.page_changed.connect(self._on_page_changed)

    def _on_page_changed(self, page_name: str):
        self.header.set_title(page_name)
