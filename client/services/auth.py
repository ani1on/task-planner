from typing import Any

from client.api.client import ApiClient
from client.api.errors import UnauthorizedError
from client.core.session_store import SessionStore


class AuthService:
    def __init__(self, api: ApiClient, session_store: SessionStore | None = None):
        self.api = api
        self.session_store = session_store or SessionStore()

        self.access_token: str | None = None
        self.refresh_token: str | None = None
        self.user: dict[str, Any] | None = None

    @property
    def is_authenticated(self) -> bool:
        return self.access_token is not None

    def register(
        self,
        email: str,
        password: str,
        nick_name: str,
    ) -> dict[str, Any]:
        response = self.api.post(
            "/auth/register",
            json={
                "email": email,
                "password": password,
                "nick_name": nick_name,
            },
        )

        return response

    def login(
        self,
        email: str,
        password: str,
    ) -> dict[str, Any]:
        response = self.api.post(
            "/auth/login",
            json={
                "email": email,
                "password": password,
            },
        )

        refresh_token = response["refresh_token"]
        self.session_store.save_refresh_token(refresh_token)

        self.refresh_token = refresh_token
        self.access_token = response["access_token"]
        self.api.set_token(self.access_token)

        self.user = self.me()

        return self.user

    def me(self) -> dict[str, Any]:
        response = self.api.get("/auth/me")

        self.user = response

        return response

    def refresh(self) -> dict[str, Any]:
        if not self.refresh_token:
            raise RuntimeError("Refresh token отсутствует")

        response = self.api.post(
            "/auth/refresh",
            json={
                "refresh_token": self.refresh_token,
            },
        )

        refresh_token = response["refresh_token"]
        self.session_store.save_refresh_token(refresh_token)

        self.access_token = response["access_token"]
        self.refresh_token = refresh_token
        self.api.set_token(self.access_token)

        return response

    def restore_session(self) -> bool:
        refresh_token = self.session_store.load_refresh_token()
        if not refresh_token:
            return False

        self.refresh_token = refresh_token
        try:
            self.refresh()
            self.user = self.me()
        except UnauthorizedError:
            self.clear_auth()
            return False

        return True

    def logout(self) -> dict[str, Any] | None:
        if not self.refresh_token:
            self.clear_auth()
            return None

        response = self.api.post(
            "/auth/logout",
            json={
                "refresh_token": self.refresh_token,
            },
        )

        self.clear_auth()

        return response

    def clear_auth(self):
        self.access_token = None
        self.refresh_token = None
        self.user = None

        self.api.set_token(None)
        self.session_store.clear()

    def change_password(
        self,
        current_password: str,
        new_password: str,
    ) -> dict[str, Any]:
        return self.api.post(
            "/auth/change-password",
            json={
                "current_password": current_password,
                "new_password": new_password,
            },
        )

    def update_profile(self, **fields: Any) -> dict[str, Any]:
        self.user = self.api.patch("/users/me", json=fields)

        return self.user

    def get_settings(self) -> dict[str, Any]:
        return self.api.get("/users/me/settings")

    def update_settings(self, **fields: Any) -> dict[str, Any]:
        return self.api.patch("/users/me/settings", json=fields)

    def forgot_password(
        self,
        email: str,
    ) -> dict[str, Any]:
        return self.api.post(
            "/auth/forgot-password",
            json={
                "email": email,
            },
        )

    def reset_password(
        self,
        token: str,
        new_password: str,
    ) -> dict[str, Any]:
        return self.api.post(
            "/auth/reset-password",
            json={
                "token": token,
                "new_password": new_password,
            },
        )
