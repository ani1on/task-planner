from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ...api.deps import get_current_user
from ...database import get_db
from ...models.user import User
from ...schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserResponse,
)
from ...schemas.common import MessageResponse
from ...services.auth import AuthService

router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)


@router.get(
    "/me",
    response_model=UserResponse,
)
def get_me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    data: RegisterRequest,
    db: Session = Depends(get_db),
) -> UserResponse:
    service = AuthService(db)

    user = service.register(data)

    db.commit()

    return UserResponse.model_validate(user)


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    data: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    service = AuthService(db)

    tokens = service.login(data)

    db.commit()

    return tokens


@router.post(
    "/refresh",
    response_model=TokenResponse,
)
def refresh(
    data: RefreshTokenRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    service = AuthService(db)

    return service.refresh(data.refresh_token)


@router.post("/logout", response_model=MessageResponse)
def logout(
    data: RefreshTokenRequest,
    db: Session = Depends(get_db),
) -> MessageResponse:
    service = AuthService(db)
    service.logout(data.refresh_token)
    db.commit()

    return MessageResponse(
        message="Successfully logged out",
    )


@router.post(
    "/change-password",
    response_model=MessageResponse,
)
def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    service = AuthService(db)

    service.change_password(
        current_user,
        data,
    )

    db.commit()

    return MessageResponse(message="Password successfully changed")


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
)
def forgot_password(
    data: ForgotPasswordRequest,
    db: Session = Depends(get_db),
) -> MessageResponse:
    service = AuthService(db)

    reset_token = service.forgot_password(data)

    db.commit()

    # todo |На production здесь должен быть вызов email-сервиса.
    # todo |Важно:
    # todo |пользователю всегда возвращаем одинаковый ответ,
    # todo |существует email или нет.
    # todo |Это предотвращает email enumeration.

    return MessageResponse(
        message="If the email is registered, a password reset link has been sent"
    )


@router.post(
    "/reset-password",
    response_model=MessageResponse,
)
def reset_password(
    data: ResetPasswordRequest,
    db: Session = Depends(get_db),
) -> MessageResponse:
    service = AuthService(db)

    service.reset_password(data)

    db.commit()

    return MessageResponse(message="Password successfully reset")
