from sqlalchemy.orm import Session

from ..core.errors import AppException
from ..models.user import User
from ..models.user_setting import UserSetting
from ..repositories.user import UserRepository
from ..repositories.user_setting import UserSettingRepository
from ..schemas.user import UserSettingUpdate, UserUpdate


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)
        self.settings = UserSettingRepository(db)

    def update_profile(self, user: User, data: UserUpdate) -> User:
        changes = data.model_dump(exclude_unset=True)

        new_nick_name = changes.get("nick_name")

        if new_nick_name is not None and new_nick_name != user.nick_name:
            existing = self.users.get_by_nick_name(new_nick_name)

            if existing is not None:
                raise AppException(
                    status_code=409,
                    detail="Nickname is already taken",
                    code="nickname_already_exists",
                )

        for field, value in changes.items():
            setattr(user, field, value)

        self.db.flush()

        return user

    def get_settings(self, user_id: int) -> UserSetting:
        setting = self.settings.get_by_user(user_id)

        if setting is None:
            setting = UserSetting(user_id=user_id)
            setting = self.settings.create(setting)

        return setting

    def update_settings(
        self,
        user_id: int,
        data: UserSettingUpdate,
    ) -> UserSetting:
        setting = self.get_settings(user_id)

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(setting, field, value)

        self.db.flush()

        return setting
