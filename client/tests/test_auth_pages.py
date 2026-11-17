import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication, QPushButton

from client.ui.pages.login_page import LoginPage
from client.ui.pages.register_page import RegisterPage


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


class FakeAuthService:
    def __init__(self):
        self.registered = []

    def register(self, **fields):
        self.registered.append(fields)


def test_login_has_no_recovery_code_or_demo_link(qapp):
    page = LoginPage(FakeAuthService())
    button_texts = {
        button.text() for button in page.findChildren(QPushButton)
    }

    assert "Забыли пароль?" in button_texts
    assert "Есть код восстановления?" not in button_texts
    assert "Посмотреть демо (без сервера)" not in button_texts


def test_registration_clears_field_error_when_input_is_fixed(qapp):
    page = RegisterPage(FakeAuthService())
    page.email_field.field.setText("invalid")
    page._validate()

    assert page.email_field.error.text() == "Некорректный email"

    page.email_field.field.setText("user@example.com")

    assert page.email_field.error.isHidden()


def test_registration_submits_and_calls_success_callback(qapp):
    service = FakeAuthService()
    registered = []
    page = RegisterPage(service, on_registered=lambda: registered.append(True))
    page.email_field.field.setText("user@example.com")
    page.name_field.field.setText("Пользователь")
    page.password_field.field.setText("password123")
    page.confirm_field.field.setText("password123")
    page.terms.setChecked(True)

    page.register()

    assert service.registered == [{
        "email": "user@example.com",
        "password": "password123",
        "nick_name": "Пользователь",
    }]
    assert registered == [True]
