from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

ACCENTS = {
    "primary": "#2563eb",
    "success": "#16a34a",
    "warning": "#d97706",
    "danger": "#dc2626",
    "purple": "#7c3aed",
}


class StatCard(QFrame):
    """Карточка со сводным показателем."""

    def __init__(
        self,
        label: str,
        value: str,
        accent: str = "primary",
        parent=None,
    ):
        super().__init__(parent)

        self.setProperty("component", "card")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        bar = QFrame()
        bar.setFixedSize(4, 38)
        bar.setStyleSheet(
            f"background-color: {ACCENTS.get(accent, ACCENTS['primary'])};"
            "border-radius: 2px;"
        )

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        value_label = QLabel(value)
        value_label.setProperty("role", "stat-value")

        caption_label = QLabel(label)
        caption_label.setProperty("role", "muted")

        text_layout.addWidget(value_label)
        text_layout.addWidget(caption_label)

        layout.addWidget(bar)
        layout.addLayout(text_layout)
        layout.addStretch()
