from client.api.errors import (
    ApiError,
    ForbiddenError,
    NetworkError,
    NotFoundError,
    ServerError,
    UnauthorizedError,
    ValidationError,
)
from client.core.session_store import SessionStoreError


def error_message(error: Exception) -> str:
    """Возвращает понятный пользователю текст ошибки API."""

    if isinstance(error, SessionStoreError):
        return str(error)

    if isinstance(
        error,
        UnauthorizedError,
    ):
        return "Сессия истекла. Войдите снова."

    if isinstance(
        error,
        ForbiddenError,
    ):
        return "У вас нет доступа к этому ресурсу."

    if isinstance(
        error,
        NotFoundError,
    ):
        return "Ресурс не найден."

    if isinstance(
        error,
        ValidationError,
    ):
        return "Проверьте введённые данные."

    if isinstance(
        error,
        ServerError,
    ):
        return "Ошибка сервера. Попробуйте позже."

    if isinstance(
        error,
        NetworkError,
    ):
        return "Не удалось подключиться к серверу."

    if isinstance(
        error,
        ApiError,
    ):
        return error.message

    return "Произошла неизвестная ошибка."


def handle_api_error(
    error: Exception,
    parent=None,
):
    from client.ui.dialogs import ErrorDialog

    dialog = ErrorDialog(
        error_message(error),
        parent,
    )

    dialog.exec()
