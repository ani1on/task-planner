import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import QThreadPool
from PySide6.QtWidgets import QApplication

from client.api.errors import UnauthorizedError
from client.services.auth import AuthService
from client.themes.manager import ThemeManager
from client.ui.app_window import AppWindow


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


class FakeSessionStore:
    def __init__(self, token=None):
        self.token = token
        self.saved = []
        self.cleared = False

    def load_refresh_token(self):
        return self.token

    def save_refresh_token(self, token):
        self.token = token
        self.saved.append(token)

    def clear(self):
        self.token = None
        self.cleared = True


class FakeApi:
    def __init__(self, fail_refresh=False):
        self.fail_refresh = fail_refresh
        self.calls = []
        self.token = None

    def post(self, path, **kwargs):
        self.calls.append(("POST", path))
        if path == "/auth/refresh":
            if self.fail_refresh:
                raise UnauthorizedError("expired", 401)
            return {"access_token": "access-new", "refresh_token": "refresh-new"}
        if path == "/auth/login":
            return {"access_token": "access-login", "refresh_token": "refresh-login"}
        raise AssertionError(f"Unexpected POST {path}")

    def get(self, path, **kwargs):
        self.calls.append(("GET", path))
        assert path == "/auth/me"
        return {"id": 7, "email": "user@example.com", "nick_name": "User"}

    def set_token(self, token):
        self.token = token


def test_auth_restores_and_rotates_persisted_refresh_token():
    store = FakeSessionStore("refresh-old")
    api = FakeApi()
    auth = AuthService(api, session_store=store)

    assert auth.restore_session() is True
    assert store.saved == ["refresh-new"]
    assert store.token == "refresh-new"
    assert api.token == "access-new"
    assert auth.user["id"] == 7
    assert api.calls == [
        ("POST", "/auth/refresh"),
        ("GET", "/auth/me"),
    ]


def test_auth_discards_expired_saved_session_without_modal_error():
    store = FakeSessionStore("expired-refresh")
    auth = AuthService(FakeApi(fail_refresh=True), session_store=store)

    assert auth.restore_session() is False
    assert store.cleared is True
    assert store.token is None
    assert auth.access_token is None


def test_login_persists_refresh_token(qapp):
    store = FakeSessionStore()
    api = FakeApi()
    auth = AuthService(api, session_store=store)

    auth.login("user@example.com", "password123")

    assert store.saved == ["refresh-login"]
    assert store.token == "refresh-login"
    assert api.token == "access-login"


def test_app_start_does_not_load_authenticated_pages_before_login(qapp):
    api = FakeApi()
    auth = AuthService(api, session_store=FakeSessionStore())
    window = AppWindow(api, auth, ThemeManager(qapp))

    assert window.main_window is None
    assert api.calls == []

    assert QThreadPool.globalInstance().waitForDone(2000)
    qapp.processEvents()

    assert window.main_window is None
    assert api.calls == []
    window.close()


def test_app_start_with_expired_saved_session_returns_to_login(qapp):
    api = FakeApi(fail_refresh=True)
    auth = AuthService(
        api,
        session_store=FakeSessionStore("expired-refresh"),
    )
    window = AppWindow(api, auth, ThemeManager(qapp))

    assert QThreadPool.globalInstance().waitForDone(2000)
    qapp.processEvents()

    assert window.main_window is None
    assert window.stack.currentWidget() is window.login_page
    assert window.login_page.submit_button.isEnabled()
    assert window.login_page.form_error.isHidden()
    window.close()
