from pathlib import Path

from PySide6.QtWidgets import QApplication


class ThemeManager:
    def __init__(self, app: QApplication):
        self.app = app

        self.current_theme = "light"

        self.themes_path = Path(__file__).parent

    def set_theme(self, theme: str):
        if theme not in ("light", "dark"):
            raise ValueError(f"Unknown theme: {theme}")

        path = self.themes_path / f"{theme}.qss"

        with open(
            path,
            "r",
            encoding="utf-8",
        ) as file:
            stylesheet = file.read()

        self.app.setStyleSheet(stylesheet)

        self.current_theme = theme

    def toggle(self):
        if self.current_theme == "light":
            self.set_theme("dark")
        else:
            self.set_theme("light")
