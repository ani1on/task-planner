from dataclasses import replace

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from client.api.client import ApiClient
from client.api.models import Notification
from client.services.notifications import NotificationService
from client.ui.components import NotificationItem, SecondaryButton
from client.ui.dialogs.confirm import ConfirmDialog
from client.ui.error_handler import handle_api_error


class NotificationsPanel(QFrame):
    changed = Signal()

    def __init__(self, api: ApiClient, parent=None):
        super().__init__(parent)
        self.api = api
        self.service = NotificationService(api)
        self.setProperty("component", "card")
        self._notifications: list[Notification] = []
        self._unread_only = False
        self._load_failed = False
        self.notification_cards: list[NotificationItem] = []

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(10)

        heading = QHBoxLayout()
        title = QLabel("Уведомления")
        title.setProperty("role", "section-title")
        heading.addWidget(title)

        self.unread_count = QLabel()
        self.unread_count.setProperty("role", "notification-count")
        heading.addWidget(self.unread_count)
        heading.addStretch()

        close_button = QPushButton("×")
        close_button.setProperty("icon", "true")
        close_button.setFixedSize(32, 32)
        close_button.setToolTip("Скрыть уведомления")
        close_button.clicked.connect(self.hide)
        heading.addWidget(close_button)
        root.addLayout(heading)

        subtitle = QLabel("Важные обновления по задачам и проектам")
        subtitle.setProperty("role", "muted")
        root.addWidget(subtitle)

        controls = QHBoxLayout()
        controls.setSpacing(8)
        self.all_button = QPushButton("Все")
        self.unread_button = QPushButton("Непрочитанные")
        for button in (self.all_button, self.unread_button):
            button.setProperty("chip", "true")
            button.setCheckable(True)
        self.filter_group = QButtonGroup(self)
        self.filter_group.setExclusive(True)
        self.filter_group.addButton(self.all_button)
        self.filter_group.addButton(self.unread_button)
        self.all_button.setChecked(True)
        self.all_button.clicked.connect(self._show_all)
        self.unread_button.clicked.connect(self._show_unread)
        controls.addWidget(self.all_button)
        controls.addWidget(self.unread_button)
        controls.addStretch()

        self.mark_all_button = SecondaryButton("Прочитать все")
        self.mark_all_button.clicked.connect(self.mark_all)
        controls.addWidget(self.mark_all_button)
        root.addLayout(controls)

        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("NotificationScroll")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setMinimumHeight(130)
        self.scroll_area.setMaximumHeight(330)

        self.items_host = QWidget()
        self.items_layout = QVBoxLayout(self.items_host)
        self.items_layout.setContentsMargins(2, 2, 2, 2)
        self.items_layout.setSpacing(8)
        self.scroll_area.setWidget(self.items_host)
        root.addWidget(self.scroll_area)

        self.reload()

    def reload(self):
        try:
            notifications = self.service.list()
        except Exception as error:
            self._notifications = []
            self._load_failed = True
            self._render()
            handle_api_error(error, self)
            return

        self._notifications = sorted(
            notifications,
            key=lambda item: item.created_at.timestamp() if item.created_at else 0,
            reverse=True,
        )
        self._load_failed = False
        self._render()

    def _render(self):
        while self.items_layout.count():
            item = self.items_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.hide()
                widget.deleteLater()

        self.notification_cards = []
        unread_count = sum(not item.is_read for item in self._notifications)
        self.unread_count.setText(f"Непрочитанных: {unread_count}")
        self.mark_all_button.setEnabled(unread_count > 0)
        self.mark_all_button.setVisible(unread_count > 0)
        self.unread_button.setText(f"Непрочитанные · {unread_count}")
        self.all_button.setText(f"Все · {len(self._notifications)}")

        if self._unread_only:
            visible_notifications = [
                item for item in self._notifications if not item.is_read
            ]
        else:
            visible_notifications = self._notifications

        if not visible_notifications:
            if self._load_failed:
                title = "Не удалось загрузить уведомления"
                message = "Проверьте соединение и попробуйте открыть раздел ещё раз."
            elif self._unread_only:
                title = "Непрочитанных уведомлений нет"
                message = "Вы уже просмотрели все новые события."
            else:
                title = "Пока нет уведомлений"
                message = "Новые события появятся здесь."
            self._add_empty_state(title, message)
            return

        for notification in visible_notifications:
            card = NotificationItem(notification, self.items_host)
            card.mark_read_requested.connect(self.mark_read)
            card.delete_requested.connect(self.delete_notification)
            self.notification_cards.append(card)
            self.items_layout.addWidget(card)

        self.items_layout.addStretch()

    def _add_empty_state(self, title: str, message: str):
        empty = QWidget(self.items_host)
        layout = QVBoxLayout(empty)
        layout.addStretch()

        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setProperty("role", "notification-empty-title")
        layout.addWidget(title_label)

        message_label = QLabel(message)
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setProperty("role", "muted")
        message_label.setWordWrap(True)
        layout.addWidget(message_label)

        layout.addStretch()
        self.items_layout.addWidget(empty, 1)

    def _show_all(self):
        self._unread_only = False
        self._render()

    def _show_unread(self):
        self._unread_only = True
        self._render()

    def mark_read(self, notification_id: int):
        try:
            updated = self.service.mark_read(notification_id)
        except Exception as error:
            handle_api_error(error, self)
            return

        self._notifications = [
            updated if item.id == notification_id else item
            for item in self._notifications
        ]
        self._render()
        self.changed.emit()

    def delete_notification(self, notification_id: int):
        if ConfirmDialog("Удалить уведомление?", self).exec() != (
            ConfirmDialog.DialogCode.Accepted
        ):
            return

        try:
            self.service.delete(notification_id)
        except Exception as error:
            handle_api_error(error, self)
            return

        self._notifications = [
            item for item in self._notifications if item.id != notification_id
        ]
        self._render()
        self.changed.emit()

    def mark_all(self):
        if not any(not item.is_read for item in self._notifications):
            return

        try:
            self.service.mark_all_read()
        except Exception as error:
            handle_api_error(error, self)
            return

        self._notifications = [
            replace(item, is_read=True) for item in self._notifications
        ]
        self._render()
        self.changed.emit()
