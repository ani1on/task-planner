from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.refresh_session import RefreshSession
from .base import BaseRepository


class RefreshSessionRepository(BaseRepository[RefreshSession]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, RefreshSession)

    def get_by_jti(self, jti: str) -> RefreshSession | None:
        statement = select(RefreshSession).where(RefreshSession.token_jti == jti)
        return self.db.scalar(statement)

    def revoke_all_for_user(
        self,
        user_id: int,
        now: datetime,
    ) -> None:
        statement = select(RefreshSession).where(
            RefreshSession.user_id == user_id,
            RefreshSession.revoked_at.is_(None),
        )

        sessions = self.db.scalars(statement).all()

        for session in sessions:
            session.revoked_at = now
