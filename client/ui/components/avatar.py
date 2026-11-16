from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel


class Avatar(QLabel):
    """Кружок с инициалами пользователя."""

    def __init__(
        self,
        name: str = "",
        size: int = 36,
        parent=None,
    ):
        super().__init__(parent)

        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setProperty("component", "avatar")
        self.setStyleSheet(f"border-radius: {size // 2}px;")

        self.set_name(name)

    def set_name(self, name: str):
        self.setText(self.initials(name))

    @staticmethod
    def initials(name: str) -> str:
        parts = [part for part in (name or "").split() if part]

        if not parts:
            return "?"

        if len(parts) == 1:
            return parts[0][:2].upper()

        return (parts[0][0] + parts[1][0]).upper()
