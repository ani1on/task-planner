from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
)

from client.core.validators import (
    MIN_NICKNAME_LENGTH,
    MIN_PASSWORD_LENGTH,
    is_valid_email,
)
from client.services.auth import AuthService
from client.ui.components import (
    AuthCard,
    FormError,
    FormField,
    LinkRow,
    PasswordInput,
    PrimaryButton,
    TextInput,
)
from client.ui.error_handler import error_message


class RegisterPage(QWidget):
    def __init__(
        self,
        auth_service: AuthService,
        on_registered=None,
        on_login=None,
        parent=None,
    ):
        super().__init__(parent)

        self.auth_service = auth_service
        self.on_registered = on_registered
        self.on_login = on_login

        self.setObjectName("AuthScreen")

        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)

        card = AuthCard(
            "Создать аккаунт",
            "Заполните данные, чтобы начать планировать задачи",
        )

        self.email_field = FormField(
            "Email",
            TextInput("you@example.com"),
        )
        self.name_field = FormField(
            "Имя пользователя",
            TextInput("Как вас называть"),
        )
        self.password_field = FormField(
            "Пароль",
            PasswordInput("Минимум 8 символов"),
            hint=f"Минимум {MIN_PASSWORD_LENGTH} символов",
        )
        self.confirm_field = FormField(
            "Подтверждение пароля",
            PasswordInput("Повторите пароль"),
        )

        self.fields = (
            self.email_field,
            self.name_field,
            self.password_field,
            self.confirm_field,
        )

        for field in self.fields:
            card.body.addWidget(field)
            field.field.returnPressed.connect(self.register)

        self.terms = QCheckBox("Я принимаю условия использования")
        card.body.addWidget(self.terms)

        self.form_error = FormError()
        card.body.addWidget(self.form_error)

        self.submit_button = PrimaryButton("Зарегистрироваться")
        self.submit_button.setMinimumHeight(42)
        self.submit_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.submit_button.clicked.connect(self.register)
        card.body.addWidget(self.submit_button)

        card.footer.addWidget(
            LinkRow(
                "Уже есть аккаунт?",
                "Войти",
                on_click=self.open_login,
            )
        )

        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(card)
        row.addStretch()

        root.addStretch()
        root.addLayout(row)
        root.addStretch()

        self.email_field.field.setFocus()

    def register(self):
        self.form_error.clear_message()

        if not self._validate():
            return

        self._set_loading(True)

        try:
            self.auth_service.register(
                email=self.email_field.value().strip(),
                password=self.password_field.value(),
                nick_name=self.name_field.value().strip(),
            )
        except Exception as error:
            self.form_error.show_message(error_message(error))
            return
        finally:
            self._set_loading(False)

        self._clear_form()

        if self.on_registered:
            self.on_registered()

    def open_login(self):
        if self.on_login:
            self.on_login()

    def _validate(self) -> bool:
        valid = True

        email = self.email_field.value().strip()
        name = self.name_field.value().strip()
        password = self.password_field.value()
        confirm = self.confirm_field.value()

        if not email:
            self.email_field.set_error("Введите email")
            valid = False
        elif not is_valid_email(email):
            self.email_field.set_error("Некорректный email")
            valid = False

        if not name:
            self.name_field.set_error("Введите имя пользователя")
            valid = False
        elif len(name) < MIN_NICKNAME_LENGTH:
            self.name_field.set_error("Имя слишком короткое")
            valid = False

        if not password:
            self.password_field.set_error("Введите пароль")
            valid = False
        elif len(password) < MIN_PASSWORD_LENGTH:
            self.password_field.set_error(f"Минимум {MIN_PASSWORD_LENGTH} символов")
            valid = False

        if not confirm:
            self.confirm_field.set_error("Повторите пароль")
            valid = False
        elif password and confirm != password:
            self.confirm_field.set_error("Пароли не совпадают")
            valid = False

        if valid and not self.terms.isChecked():
            self.form_error.show_message("Отметьте согласие с условиями использования")
            valid = False

        return valid

    def _set_loading(self, loading: bool):
        self.submit_button.setEnabled(not loading)
        self.submit_button.setText(
            "Регистрация..." if loading else "Зарегистрироваться"
        )

    def _clear_form(self):
        for field in self.fields:
            field.field.clear()
            field.clear_error()

        self.terms.setChecked(False)
        self.form_error.clear_message()
