from datetime import datetime, timedelta, timezone
from uuid import uuid4

from jose import JWTError
from sqlalchemy.orm import Session

from ..config import settings
from ..core.errors import AppException
from ..core.security import (
    create_access_token,
    create_password_reset_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_password_reset_token,
    verify_password,
)
from ..models.password_reset_token import PasswordResetToken
from ..models.refresh_session import RefreshSession
from ..models.user import User
from ..repositories.password_reset_token import PasswordResetTokenRepository
from ..repositories.refresh_session import RefreshSessionRepository
from ..repositories.user import UserRepository
from ..schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
)
from .email import EmailService


class AuthService:
    def __init__(self, db: Session) -> None:
        self.users = UserRepository(db)
        self.refresh_sessions = RefreshSessionRepository(db)
        self.password_reset_tokens = PasswordResetTokenRepository(db)
        self.email = EmailService()

    def register(
        self,
        data: RegisterRequest,
    ) -> User:
        existing_email = self.users.get_by_email(data.email)

        if existing_email is not None:
            raise AppException(
                status_code=409,
                detail="Email is already registered",
                code="email_already_exists",
            )

        existing_nickname = self.users.get_by_nick_name(data.nick_name)

        if existing_nickname is not None:
            raise AppException(
                status_code=409,
                detail="Nickname is already taken",
                code="nickname_already_exists",
            )

        user = User(
            email=data.email,
            password_hash=hash_password(data.password),
            nick_name=data.nick_name,
            email_verified=False,
        )

        return self.users.create(user)

    def login(self, data: LoginRequest) -> TokenResponse:
        user = self.users.get_by_email(data.email)

        if user is None:
            raise AppException(
                401,
                "Invalid email or password",
                "invalid_credentials",
            )

        if not verify_password(data.password, user.password_hash):
            raise AppException(
                401,
                "Invalid email or password",
                "invalid_credentials",
            )

        now = datetime.now(timezone.utc)

        expires_at = now + timedelta(days=settings.jwt_refresh_token_expire_days)

        jti = str(uuid4())

        session = RefreshSession(
            user_id=user.id,
            token_jti=jti,
            expires_at=expires_at,
        )

        self.refresh_sessions.create(session)

        return TokenResponse(
            access_token=create_access_token(str(user.id)),
            refresh_token=create_refresh_token(
                str(user.id),
                jti,
                expires_at,
            ),
        )

    def refresh(self, refresh_token: str) -> TokenResponse:
        try:
            payload = decode_token(refresh_token)
        except JWTError:
            raise AppException(
                401,
                "Invalid or expired refresh token",
                "invalid_refresh_token",
            )

        if payload.get("type") != "refresh":
            raise AppException(
                401,
                "Invalid refresh token",
                "invalid_refresh_token",
            )

        subject = payload.get("sub")
        jti = payload.get("jti")

        if subject is None or jti is None:
            raise AppException(
                401,
                "Invalid refresh token",
                "invalid_refresh_token",
            )

        try:
            user_id = int(subject)
        except (TypeError, ValueError):
            raise AppException(
                401,
                "Invalid refresh token",
                "invalid_refresh_token",
            )

        session = self.refresh_sessions.get_by_jti(jti)

        if session is None:
            raise AppException(
                401,
                "Refresh session not found",
                "session_not_found",
            )

        now = datetime.now(timezone.utc)

        if session.revoked_at is not None:
            raise AppException(
                401,
                "Refresh session has been revoked",
                "session_revoked",
            )

        if session.expires_at <= now:
            raise AppException(
                401,
                "Refresh session has expired",
                "session_expired",
            )

        user = self.users.get_by_id(user_id)

        if user is None:
            raise AppException(
                401,
                "User not found",
                "user_not_found",
            )

        # Старую refresh-сессию отзываем.
        session.revoked_at = now
        session.last_used_at = now

        # Создаём новую refresh-сессию.
        new_jti = str(uuid4())

        new_expires_at = now + timedelta(days=settings.jwt_refresh_token_expire_days)

        new_session = RefreshSession(
            user_id=user.id,
            token_jti=new_jti,
            expires_at=new_expires_at,
        )

        self.refresh_sessions.create(new_session)

        return TokenResponse(
            access_token=create_access_token(str(user.id)),
            refresh_token=create_refresh_token(
                str(user.id),
                new_jti,
                new_expires_at,
            ),
        )

    def logout(self, refresh_token: str) -> None:
        try:
            payload = decode_token(refresh_token)
        except JWTError:
            raise AppException(
                401,
                "Invalid or expired refresh token",
                "invalid_refresh_token",
            )

        if payload.get("type") != "refresh":
            raise AppException(
                401,
                "Invalid refresh token",
                "invalid_refresh_token",
            )

        jti = payload.get("jti")

        if not jti:
            raise AppException(
                401,
                "Invalid refresh token",
                "invalid_refresh_token",
            )

        session = self.refresh_sessions.get_by_jti(jti)

        if session is None:
            raise AppException(
                401,
                "Refresh session not found",
                "session_not_found",
            )

        if session.revoked_at is not None:
            return

        session.revoked_at = datetime.now(timezone.utc)

    def change_password(
        self,
        user: User,
        data: ChangePasswordRequest,
    ) -> None:
        if not verify_password(
            data.current_password,
            user.password_hash,
        ):
            raise AppException(
                400,
                "Current password is incorrect",
                "invalid_current_password",
            )

        if data.current_password == data.new_password:
            raise AppException(
                400,
                "New password must be different from current password",
                "same_password",
            )

        user.password_hash = hash_password(data.new_password)

        now = datetime.now(timezone.utc)

        self.refresh_sessions.revoke_all_for_user(
            user.id,
            now,
        )

    def forgot_password(
        self,
        data: ForgotPasswordRequest,
    ) -> None:
        user = self.users.get_by_email(data.email)

        if user is None:
            return

        raw_token = create_password_reset_token()
        token_hash = hash_password_reset_token(raw_token)

        now = datetime.now(timezone.utc)

        expires_at = now + timedelta(
            minutes=settings.jwt_password_reset_token_expire_minutes
        )

        self.password_reset_tokens.invalidate_user_tokens(
            user.id,
            now,
        )

        reset_token = PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
        )

        self.password_reset_tokens.create(reset_token)

        self.email.send_password_reset_email(
            user.email,
            raw_token,
        )

    def reset_password(
        self,
        data: ResetPasswordRequest,
    ) -> None:
        token_hash = hash_password_reset_token(data.token)

        reset_token = self.password_reset_tokens.get_by_hash(token_hash)

        if reset_token is None:
            raise AppException(
                400,
                "Invalid reset token",
                "invalid_reset_token",
            )

        now = datetime.now(timezone.utc)

        if reset_token.used_at is not None:
            raise AppException(
                400,
                "Reset token has already been used",
                "reset_token_used",
            )

        if reset_token.expires_at <= now:
            raise AppException(
                400,
                "Reset token has expired",
                "reset_token_expired",
            )

        user = self.users.get_by_id(reset_token.user_id)

        if user is None:
            raise AppException(
                400,
                "User not found",
                "user_not_found",
            )

        user.password_hash = hash_password(data.new_password)

        reset_token.used_at = now

        self.refresh_sessions.revoke_all_for_user(
            user.id,
            now,
        )

        self.password_reset_tokens.invalidate_user_tokens(
            user.id,
            now,
        )
