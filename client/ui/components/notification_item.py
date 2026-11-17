from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from client.api.mapper import format_relative
from client.api.models import Notification


class NotificationItem(QFrame):
    mark_read_requested = Signal(int)
    delete_requested = Signal(int)

    def __init__(self, notification: Notification, parent=None):
        super().__init__(parent)
        self.notification_id = notification.id
        self.setProperty("component", "notification")
        self.setProperty("unread", not notification.is_read)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(12)

        dot = QLabel()
        dot.setFixedSize(8, 8)
        dot.setProperty(
            "component",
            "read-dot" if notification.is_read else "unread-dot",
        )
        dot.setToolTip(
            "Прочитано" if notification.is_read else "Непрочитанное уведомление"
        )

        content = QVBoxLayout()
        content.setSpacing(5)

        heading = QHBoxLayout()
        heading.setSpacing(10)

        title = QLabel(notification.title or "Уведомление")
        title.setProperty("role", "notification-title")
        title.setWordWrap(True)

        created_at = QLabel(
            format_relative(notification.created_at) or "Дата не указана"
        )
        created_at.setProperty("role", "notification-time")
        created_at.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )

        heading.addWidget(title, 1)
        heading.addWidget(created_at, 0)
        content.addLayout(heading)

        if notification.text:
            message = QLabel(notification.text)
            message.setProperty("role", "muted")
            message.setWordWrap(True)
            content.addWidget(message)

        actions = QHBoxLayout()
        actions.setSpacing(8)
        actions.addStretch()

        if not notification.is_read:
            mark_read = QPushButton("Отметить прочитанным")
            mark_read.setProperty("notificationAction", "true")
            mark_read.setCursor(Qt.CursorShape.PointingHandCursor)
            mark_read.clicked.connect(
                lambda: self.mark_read_requested.emit(self.notification_id)
            )
            actions.addWidget(mark_read)

        delete = QPushButton("Удалить")
        delete.setProperty("notificationAction", "true")
        delete.setProperty("danger", "true")
        delete.setCursor(Qt.CursorShape.PointingHandCursor)
        delete.clicked.connect(
            lambda: self.delete_requested.emit(self.notification_id)
        )
        actions.addWidget(delete)
        content.addLayout(actions)

        layout.addWidget(dot, 0, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(content, 1)
