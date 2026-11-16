from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
)

from client.api.errors import UnauthorizedError
from client.core.validators import is_valid_email
from client.services.auth import AuthService
from client.ui.components import (
    AuthCard,
    FormError,
    FormField,
    LinkButton,
    LinkRow,
    PasswordInput,
    PrimaryButton,
    TextInput,
)
from client.ui.error_handler import error_message


class LoginPage(QWidget):
    def __init__(
        self,
        auth_service: AuthService,
        on_login=None,
        on_register=None,
        on_demo=None,
        parent=None,
    ):
        super().__init__(parent)

        self.auth_service = auth_service
        self.on_login = on_login
        self.on_register = on_register
        self.on_demo = on_demo

        self.setObjectName("AuthScreen")

        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)

        card = AuthCard(
            "Вход в аккаунт",
            "Рады видеть вас снова",
        )

        self.email_field = FormField(
            "Email",
            TextInput("you@example.com"),
        )
        self.password_field = FormField(
            "Пароль",
            PasswordInput("Ваш пароль"),
        )

        self.fields = (
            self.email_field,
            self.password_field,
        )

        for field in self.fields:
            card.body.addWidget(field)
            field.field.returnPressed.connect(self.login)

        forgot_row = QHBoxLayout()
        forgot_row.addStretch()
        forgot_row.addWidget(LinkButton("Забыли пароль?", self.forgot_password))
        card.body.addLayout(forgot_row)

        self.form_error = FormError()
        card.body.addWidget(self.form_error)

        self.submit_button = PrimaryButton("Войти")
        self.submit_button.setMinimumHeight(42)
        self.submit_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.submit_button.clicked.connect(self.login)
        card.body.addWidget(self.submit_button)

        card.footer.addWidget(
            LinkRow(
                "Нет аккаунта?",
                "Зарегистрироваться",
                on_click=self.open_register,
            )
        )

        # Временная кнопка: открывает каркас без запущенного backend.
        self.demo_button = LinkButton(
            "Посмотреть демо (без сервера)",
            self.open_demo,
        )
        card.footer.addWidget(
            self.demo_button,
            0,
            Qt.AlignmentFlag.AlignHCenter,
        )

        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(card)
        row.addStretch()

        root.addStretch()
        root.addLayout(row)
        root.addStretch()

        self.email_field.field.setFocus()

    def login(self):
        self.form_error.clear_message()

        if not self._validate():
            return

        self._set_loading(True)

        try:
            user = self.auth_service.login(
                email=self.email_field.value().strip(),
                password=self.password_field.value(),
            )
        except Exception as error:
            self._show_error(error)
            return
        finally:
            self._set_loading(False)

        self.password_field.field.clear()

        if self.on_login:
            self.on_login(user)

    def forgot_password(self):
        self.form_error.clear_message()

        email = self.email_field.value().strip()

        if not is_valid_email(email):
            self.email_field.set_error("Укажите email, чтобы восстановить пароль")
            return

        self.email_field.clear_error()

        try:
            self.auth_service.forgot_password(email)
        except Exception as error:
            self.form_error.show_message(error_message(error))
            return

        self.form_error.show_message(
            "Если email зарегистрирован, ссылка для восстановления отправлена.",
            variant="success",
        )

    def open_register(self):
        if self.on_register:
            self.on_register()

    def open_demo(self):
        if self.on_demo:
            self.on_demo()

    def _validate(self) -> bool:
        valid = True

        email = self.email_field.value().strip()
        password = self.password_field.value()

        if not email:
            self.email_field.set_error("Введите email")
            valid = False
        elif not is_valid_email(email):
            self.email_field.set_error("Некорректный email")
            valid = False

        if not password:
            self.password_field.set_error("Введите пароль")
            valid = False

        return valid

    def _show_error(self, error: Exception):
        if isinstance(error, UnauthorizedError):
            self.form_error.show_message("Неверный email или пароль")
            return

        self.form_error.show_message(error_message(error))

    def _set_loading(self, loading: bool):
        self.submit_button.setEnabled(not loading)
        self.submit_button.setText("Вход..." if loading else "Войти")
