from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.user_setting import UserSetting
from .base import BaseRepository


class UserSettingRepository(BaseRepository[UserSetting]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, UserSetting)

    def get_by_user(self, user_id: int) -> UserSetting | None:
        statement = select(UserSetting).where(UserSetting.user_id == user_id)

        return self.db.scalar(statement)
