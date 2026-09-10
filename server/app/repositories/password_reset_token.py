from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.password_reset_token import PasswordResetToken
from .base import BaseRepository


class PasswordResetTokenRepository(BaseRepository[PasswordResetToken]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, PasswordResetToken)

    def get_by_hash(self, token_hash: str) -> PasswordResetToken | None:
        statement = select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash
        )
        return self.db.scalar(statement)

    def invalidate_user_tokens(
        self,
        user_id: int,
        now: datetime,
    ) -> None:
        statement = select(PasswordResetToken).where(
            PasswordResetToken.user_id == user_id,
            PasswordResetToken.used_at.is_(None),
        )

        tokens = self.db.scalars(statement).all()

        for token in tokens:
            token.used_at = now
