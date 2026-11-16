from sqlalchemy.orm import Session

from ..core.errors import AppException
from ..models.tag import Tag
from ..repositories.project import ProjectRepository
from ..repositories.tag import TagRepository
from ..schemas.tag import TagCreate, TagUpdate
from .access import AccessService
from .activity import ActivityService


class TagService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.tags = TagRepository(db)
        self.projects = ProjectRepository(db)
        self.access = AccessService(db)
        self.activity = ActivityService(db)

    def list(
        self,
        user_id: int,
        project_id: int | None = None,
    ) -> list[Tag]:
        return self.tags.list_for_user(user_id, project_id)

    def get(
        self,
        tag_id: int,
        user_id: int,
    ) -> Tag:
        tag = self.tags.get_for_user(tag_id, user_id)

        if tag is None:
            raise AppException(
                status_code=404,
                detail="Tag not found",
                code="tag_not_found",
            )

        return tag

    def create(
        self,
        user_id: int,
        data: TagCreate,
    ) -> Tag:
        project = self.projects.get_for_user(data.project_id, user_id)

        if project is None:
            raise AppException(
                status_code=404,
                detail="Project not found",
                code="project_not_found",
            )

        self.access.require_role(data.project_id, user_id, "member")

        existing = self.tags.get_by_name(data.project_id, data.name)

        if existing is not None:
            raise AppException(
                status_code=409,
                detail="Tag with this name already exists",
                code="tag_already_exists",
            )

        tag = Tag(
            project_id=data.project_id,
            name=data.name,
            color=data.color,
        )

        return self.tags.create(tag)

    def update(
        self,
        tag: Tag,
        user_id: int,
        data: TagUpdate,
    ) -> Tag:
        self.access.require_role(tag.project_id, user_id, "member")

        changes = data.model_dump(exclude_unset=True)

        new_name = changes.get("name")

        if new_name is not None and new_name != tag.name:
            existing = self.tags.get_by_name(tag.project_id, new_name)

            if existing is not None:
                raise AppException(
                    status_code=409,
                    detail="Tag with this name already exists",
                    code="tag_already_exists",
                )

        old_values = {
            field: getattr(tag, field)
            for field in changes
        }

        for field, value in changes.items():
            setattr(tag, field, value)

        self.db.flush()

        self.activity.log(
            user_id=user_id,
            action="tag_updated",
            entity_type="tag",
            entity_id=tag.id,
            project_id=tag.project_id,
            old_values=old_values,
            new_values=changes,
        )

        return tag

    def delete(
        self,
        tag: Tag,
        user_id: int,
    ) -> None:
        self.access.require_role(tag.project_id, user_id, "member")

        self.activity.log(
            user_id=user_id,
            action="tag_deleted",
            entity_type="tag",
            entity_id=tag.id,
            project_id=tag.project_id,
            old_values={"name": tag.name},
        )

        self.tags.delete(tag)
