import sys

from PySide6.QtWidgets import QApplication

from client.api.client import ApiClient
from client.core.config import Config
from client.services.auth import AuthService


def main():
    app = QApplication(sys.argv)

    api = ApiClient(
        base_url=Config.API_URL,
        timeout=Config.API_TIMEOUT,
    )

    auth = AuthService(api)

    email = input("Email: ")
    nick_name = input("Nick name: ")
    password = input("Password: ")

    try:
        user = auth.register(
            email=email,
            password=password,
            nick_name=nick_name,
        )

        print()
        print("=== РЕГИСТРАЦИЯ ===")
        print(user)

        user = auth.login(
            email=email,
            password=password,
        )

        print()
        print("=== LOGIN ===")
        print(user)

        print()
        print("=== TOKENS ===")
        print("Access token:", auth.access_token)
        print("Refresh token:", auth.refresh_token)

        print()
        print("=== /auth/me ===")
        print(auth.me())

    except Exception as error:
        print()
        print("ОШИБКА:")
        print(type(error).__name__)
        print(error)

    sys.exit()


if __name__ == "__main__":
    main()
