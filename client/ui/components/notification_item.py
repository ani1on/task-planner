from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout


class NotificationItem(QFrame):
    """Строка в списке уведомлений."""

    def __init__(self, notification: dict, parent=None):
        super().__init__(parent)

        self.setProperty("component", "notification")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        dot = QLabel()
        dot.setFixedSize(8, 8)
        dot.setProperty(
            "component",
            "unread-dot" if notification.get("unread") else "read-dot",
        )

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        title = QLabel(notification.get("title", ""))
        title.setProperty("role", "task-title")

        text = QLabel(notification.get("text", ""))
        text.setProperty("role", "muted")
        text.setWordWrap(True)

        time_label = QLabel(notification.get("time", ""))
        time_label.setProperty("role", "muted")

        text_layout.addWidget(title)
        text_layout.addWidget(text)
        text_layout.addWidget(time_label)

        layout.addWidget(dot, 0, 0)
        layout.addLayout(text_layout, 1)
