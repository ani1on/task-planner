import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication, QPushButton

from client.ui.dialogs.notifications import NotificationsPanel


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


class FakeApi:
    def __init__(self):
        self.notifications = [
            {
                "id": 1,
                "title": "Старая заметка",
                "text": "Уведомление уже прочитано",
                "is_read": True,
                "created_at": "2026-11-16T10:00:00+00:00",
            },
            {
                "id": 2,
                "title": "Новая задача",
                "text": "Вам назначена задача",
                "is_read": False,
                "created_at": "2026-11-17T10:00:00+00:00",
            },
            {
                "id": 3,
                "title": "Новый комментарий",
                "text": "Добавлен комментарий",
                "is_read": False,
                "created_at": "2026-11-18T10:00:00+00:00",
            },
        ]

    def get(self, path, **kwargs):
        assert path == "/notifications"
        return self.notifications

    def post(self, path, **kwargs):
        notification_id = int(path.split("/")[2])
        notification = next(
            item for item in self.notifications if item["id"] == notification_id
        )
        notification["is_read"] = True
        return notification


def test_notifications_panel_filters_and_orders_cards(qapp):
    panel = NotificationsPanel(FakeApi())

    cards = panel.notification_cards
    assert [card.notification_id for card in cards] == [3, 2, 1]
    assert panel.unread_count.text() == "Непрочитанных: 2"

    panel.unread_button.click()
    qapp.processEvents()

    cards = panel.notification_cards
    assert [card.notification_id for card in cards] == [3, 2]
    assert panel.all_button.isChecked() is False
    assert panel.unread_button.isChecked() is True


def test_notifications_panel_marks_selected_card_read(qapp):
    panel = NotificationsPanel(FakeApi())
    changed = []
    panel.changed.connect(lambda: changed.append(True))

    card = next(card for card in panel.notification_cards if card.notification_id == 3)
    mark_read = next(
        button
        for button in card.findChildren(QPushButton)
        if button.text() == "Отметить прочитанным"
    )
    mark_read.click()
    qapp.processEvents()

    assert all(item.is_read for item in panel._notifications if item.id == 3)
    assert panel.unread_count.text() == "Непрочитанных: 1"
    assert changed == [True]
