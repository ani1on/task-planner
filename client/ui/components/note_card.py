from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
)

from .badge import Badge


class NoteCard(QFrame):
    """Карточка заметки."""

    def __init__(self, note: dict, parent=None):
        super().__init__(parent)

        self.setProperty("component", "card")
        self.setProperty("clickable", "true")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(8)

        title = QLabel(note.get("title", ""))
        title.setProperty("role", "card-title")

        preview = QLabel(note.get("preview", ""))
        preview.setProperty("role", "muted")
        preview.setWordWrap(True)

        footer = QHBoxLayout()
        footer.setSpacing(6)

        project = note.get("project")
        if project:
            footer.addWidget(Badge(project, "neutral"))

        footer.addStretch()

        updated = QLabel(note.get("updated", ""))
        updated.setProperty("role", "muted")
        footer.addWidget(updated)

        layout.addWidget(title)
        layout.addWidget(preview)
        layout.addStretch()
        layout.addLayout(footer)
