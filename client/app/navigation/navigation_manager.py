from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QStackedWidget, QWidget


class NavigationManager(QObject):
    page_changed = Signal(str)

    def __init__(self, stack: QStackedWidget):
        super().__init__()

        self.stack = stack
        self._pages: dict[str, QWidget] = {}

    def register_page(self, name: str, page: QWidget):
        """
        Регистрирует страницу в системе навигации.
        """
        if name in self._pages:
            raise ValueError(f"Page '{name}' is already registered")

        self._pages[name] = page
        self.stack.addWidget(page)

    def navigate(self, name: str):
        """
        Переключает приложение на указанную страницу.
        """
        page = self._pages.get(name)

        if page is None:
            raise ValueError(f"Page '{name}' is not registered")

        self.stack.setCurrentWidget(page)
        self.page_changed.emit(name)

    def current_page(self) -> str | None:
        """
        Возвращает имя текущей страницы.
        """
        current_widget = self.stack.currentWidget()

        for name, page in self._pages.items():
            if page is current_widget:
                return name

        return None

    def has_page(self, name: str) -> bool:
        return name in self._pages
