from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.user import User
from .base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, User)

    def get_by_email(
        self,
        email: str,
    ) -> User | None:
        statement = select(User).where(User.email == email)

        return self.db.scalar(statement)

    def get_by_nick_name(
        self,
        nick_name: str,
    ) -> User | None:
        statement = select(User).where(User.nick_name == nick_name)

        return self.db.scalar(statement)
