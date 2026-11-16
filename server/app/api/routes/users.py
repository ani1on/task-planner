from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...api.deps import get_current_user
from ...database import get_db
from ...models.user import User
from ...schemas.auth import UserResponse
from ...schemas.user import UserSettingResponse, UserSettingUpdate, UserUpdate
from ...services.user import UserService

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.patch("/me", response_model=UserResponse)
def update_me(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    service = UserService(db)

    user = service.update_profile(current_user, data)

    db.commit()

    return UserResponse.model_validate(user)


@router.get("/me/settings", response_model=UserSettingResponse)
def get_my_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserSettingResponse:
    service = UserService(db)

    setting = service.get_settings(current_user.id)

    db.commit()

    return UserSettingResponse.model_validate(setting)


@router.patch("/me/settings", response_model=UserSettingResponse)
def update_my_settings(
    data: UserSettingUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserSettingResponse:
    service = UserService(db)

    setting = service.update_settings(current_user.id, data)

    db.commit()

    return UserSettingResponse.model_validate(setting)
