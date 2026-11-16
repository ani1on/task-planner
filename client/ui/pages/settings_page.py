from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
)

from client.services.auth import AuthService
from client.ui.components import (
    Avatar,
    DangerButton,
    SecondaryButton,
    SectionTitle,
)
from client.ui.dialogs import ErrorDialog, PasswordDialog, ProfileDialog
from client.ui.error_handler import handle_api_error

from .base_page import BasePage


class SettingsPage(BasePage):
    theme_toggled = Signal()
    logout_requested = Signal()

    def __init__(
        self,
        user: dict | None = None,
        auth_service: AuthService | None = None,
        parent=None,
    ):
        super().__init__("Настройки", "Профиль, внешний вид и уведомления")

        self.auth_service = auth_service

        self._build_profile(user)
        self._build_appearance()
        self._build_notifications()
        self._build_account()

    def _section(self, title: str) -> QVBoxLayout:
        card = QFrame()
        card.setProperty("component", "card")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(14)

        layout.addWidget(SectionTitle(title))

        self.content_layout.addWidget(card)

        return layout

    def _build_profile(self, user: dict | None):
        layout = self._section("Профиль")

        row = QHBoxLayout()
        row.setSpacing(14)

        self.profile_avatar = Avatar("", size=56)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        self.profile_name = QLabel()
        self.profile_name.setProperty("role", "card-title")

        self.profile_email = QLabel()
        self.profile_email.setProperty("role", "muted")

        text_layout.addWidget(self.profile_name)
        text_layout.addWidget(self.profile_email)

        row.addWidget(self.profile_avatar)
        row.addLayout(text_layout)
        row.addStretch()

        change_profile = SecondaryButton("Изменить")
        change_profile.clicked.connect(self.edit_profile)

        row.addWidget(change_profile)

        layout.addLayout(row)

        self.set_user(user)

    def set_user(self, user: dict | None):
        user = user or {}

        name = user.get("nick_name") or "Гость"
        email = user.get("email") or "Нет данных"

        self.profile_avatar.set_name(name)
        self.profile_name.setText(name)
        self.profile_email.setText(email)

    def edit_profile(self):
        if self.auth_service is None:
            return

        dialog = ProfileDialog(self.auth_service.user or {}, self)

        if dialog.exec() != ProfileDialog.DialogCode.Accepted:
            return

        try:
            user = self.auth_service.update_profile(**dialog.values())
        except Exception as error:
            handle_api_error(error, self)
            return

        self.set_user(user)

    def _build_appearance(self):
        layout = self._section("Внешний вид")

        row = QHBoxLayout()
        row.setSpacing(14)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        title = QLabel("Тема оформления")
        title.setProperty("role", "card-title")

        description = QLabel("Светлая или тёмная тема интерфейса")
        description.setProperty("role", "muted")

        text_layout.addWidget(title)
        text_layout.addWidget(description)

        button = SecondaryButton("Переключить тему")
        button.clicked.connect(self.theme_toggled.emit)

        row.addLayout(text_layout)
        row.addStretch()
        row.addWidget(button)

        layout.addLayout(row)

    def _build_notifications(self):
        layout = self._section("Уведомления")

        self.notifications_checkbox = QCheckBox("Включить уведомления")
        self.notifications_checkbox.setChecked(True)
        self.notifications_checkbox.toggled.connect(self.save_notifications)

        layout.addWidget(self.notifications_checkbox)

    def save_notifications(self, enabled: bool):
        if self.auth_service is None:
            return

        try:
            self.auth_service.update_settings(notification_enabled=enabled)
        except Exception as error:
            handle_api_error(error, self)

    def refresh_settings(self):
        if self.auth_service is None:
            return

        try:
            settings = self.auth_service.get_settings()
        except Exception:
            return

        self.notifications_checkbox.blockSignals(True)
        self.notifications_checkbox.setChecked(
            settings.get("notification_enabled", True)
        )
        self.notifications_checkbox.blockSignals(False)

    def _build_account(self):
        layout = self._section("Аккаунт")

        row = QHBoxLayout()
        row.setSpacing(8)

        change_password = SecondaryButton("Сменить пароль")
        change_password.clicked.connect(self.change_password)

        logout = DangerButton("Выйти")
        logout.clicked.connect(self.logout_requested.emit)

        row.addWidget(change_password)
        row.addWidget(logout)
        row.addStretch()

        layout.addLayout(row)

    def change_password(self):
        if self.auth_service is None:
            return

        dialog = PasswordDialog(self)

        if dialog.exec() != PasswordDialog.DialogCode.Accepted:
            return

        current_password, new_password = dialog.values()

        if len(new_password) < 8:
            ErrorDialog(
                "Новый пароль должен содержать минимум 8 символов.",
                self,
            ).exec()
            return

        try:
            self.auth_service.change_password(
                current_password,
                new_password,
            )
        except Exception as error:
            handle_api_error(error, self)
            return

        ErrorDialog("Пароль успешно изменён.", self).exec()
