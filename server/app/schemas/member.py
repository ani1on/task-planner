from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

ProjectRole = Literal["admin", "member", "viewer"]


class MemberUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nick_name: str
    email: EmailStr
    avatar_url: str


class MemberInvite(BaseModel):
    email: EmailStr | None = None
    user_id: int | None = None
    role: ProjectRole = "member"

    @model_validator(mode="after")
    def check_target(self) -> "MemberInvite":
        if (self.email is None) == (self.user_id is None):
            raise ValueError("Provide either email or user_id")

        return self


class MemberUpdate(BaseModel):
    role: ProjectRole


class MemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    user_id: int
    role: str
    joined_at: datetime
    user: MemberUser


class ProjectAccessResponse(BaseModel):
    project_id: int
    role: str = Field(min_length=1, max_length=20)
