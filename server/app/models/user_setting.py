from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from .user import User


class UserSetting(Base):
    __tablename__ = "user_settings"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    theme: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="light",
    )

    timezone: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        server_default="UTC",
    )

    notification_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="True",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="settings",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<UserSetting(user_id={self.user_id}, theme={self.theme})>"
