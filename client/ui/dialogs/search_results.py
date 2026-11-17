from PySide6.QtWidgets import (
    QListWidget,
    QListWidgetItem,
)

from client.api.client import ApiClient
from client.ui.error_handler import handle_api_error

from .base import BaseDialog


class SearchResultsDialog(BaseDialog):
    def __init__(self, api: ApiClient, query: str, parent=None):
        super().__init__(parent)
        self.api = api
        self.setWindowTitle(f"Поиск: {query}")
        self.resize(520, 420)

        self.list_widget = QListWidget()
        self.layout.addWidget(self.list_widget)

        self.load(query)

    def load(self, query: str):
        self.list_widget.clear()
        try:
            results = self.api.get("/search", params={"q": query}) or {}
        except Exception as error:
            handle_api_error(error, self)
            return

        items = []
        for key in ("tasks", "projects", "notes"):
            for entry in results.get(key, []) or []:
                title = entry.get("title") or entry.get("name") or str(entry)
                items.append(f"[{key}] {title}")

        if not items:
            items.append("Ничего не найдено")

        for text in items:
            self.list_widget.addItem(QListWidgetItem(text))
