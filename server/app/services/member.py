from sqlalchemy.orm import Session

from ..core.errors import AppException
from ..models.project import Project
from ..models.project_member import ProjectMember
from ..realtime import events, project_room, publish, user_room
from ..repositories.project import ProjectRepository
from ..repositories.project_member import ProjectMemberRepository
from ..repositories.user import UserRepository
from ..schemas.member import MemberInvite, MemberUpdate
from .access import AccessService
from .activity import ActivityService
from .notification import NotificationService


class MemberService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.members = ProjectMemberRepository(db)
        self.projects = ProjectRepository(db)
        self.users = UserRepository(db)
        self.access = AccessService(db)
        self.activity = ActivityService(db)
        self.notifications = NotificationService(db)

    def list(
        self,
        project_id: int,
        user_id: int,
    ) -> tuple[Project, list[ProjectMember]]:
        self.access.require_role(project_id, user_id, "viewer")

        project = self.projects.get_by_id(project_id)

        if project is None:
            raise AppException(
                status_code=404,
                detail="Project not found",
                code="project_not_found",
            )

        return project, self.members.list_for_project(project_id)

    def add(
        self,
        project_id: int,
        actor_id: int,
        data: MemberInvite,
    ) -> ProjectMember:
        self.access.require_role(project_id, actor_id, "admin")

        project = self.projects.get_by_id(project_id)

        if project is None:
            raise AppException(
                status_code=404,
                detail="Project not found",
                code="project_not_found",
            )

        user = (
            self.users.get_by_email(data.email)
            if data.email is not None
            else self.users.get_by_id(data.user_id)
        )

        if user is None:
            raise AppException(
                status_code=404,
                detail="User not found",
                code="user_not_found",
            )

        if user.id == project.owner_id or self.members.get(project_id, user.id):
            raise AppException(
                status_code=409,
                detail="User is already a project member",
                code="member_already_exists",
            )

        member = self.members.create(
            ProjectMember(
                project_id=project_id,
                user_id=user.id,
                role=data.role,
            ),
        )

        self.activity.log(
            user_id=actor_id,
            action="member_added",
            entity_type="project_member",
            entity_id=member.id,
            project_id=project_id,
            new_values={"user_id": user.id, "role": member.role},
        )

        self.notifications.notify(
            user_id=user.id,
            type="project_invitation",
            title="Приглашение в проект",
            message=f"Вас добавили в проект «{project.name}»",
            project_id=project_id,
            actor_id=actor_id,
        )

        publish(
            project_room(project_id),
            events.MEMBER_ADDED,
            {
                "project_id": project_id,
                "user_id": user.id,
                "role": member.role,
            },
        )

        publish(
            user_room(user.id),
            events.MEMBER_ADDED,
            {
                "project_id": project_id,
                "role": member.role,
            },
        )

        return member

    def update_role(
        self,
        project_id: int,
        actor_id: int,
        target_user_id: int,
        data: MemberUpdate,
    ) -> ProjectMember:
        self.access.require_role(project_id, actor_id, "admin")

        project = self.projects.get_by_id(project_id)

        if project is not None and project.owner_id == target_user_id:
            raise AppException(
                status_code=400,
                detail="Project owner role cannot be changed",
                code="owner_role_immutable",
            )

        member = self.members.get(project_id, target_user_id)

        if member is None:
            raise AppException(
                status_code=404,
                detail="Project member not found",
                code="member_not_found",
            )

        old_role = member.role
        member.role = data.role

        self.db.flush()

        self.activity.log(
            user_id=actor_id,
            action="member_role_updated",
            entity_type="project_member",
            entity_id=member.id,
            project_id=project_id,
            old_values={"role": old_role},
            new_values={"role": member.role},
        )

        publish(
            project_room(project_id),
            events.MEMBER_UPDATED,
            {
                "project_id": project_id,
                "user_id": target_user_id,
                "role": member.role,
            },
        )

        return member

    def remove(
        self,
        project_id: int,
        actor_id: int,
        target_user_id: int,
    ) -> None:
        self.access.require_role(project_id, actor_id, "admin")

        project = self.projects.get_by_id(project_id)

        if project is not None and project.owner_id == target_user_id:
            raise AppException(
                status_code=400,
                detail="Project owner cannot be removed",
                code="owner_cannot_be_removed",
            )

        member = self.members.get(project_id, target_user_id)

        if member is None:
            raise AppException(
                status_code=404,
                detail="Project member not found",
                code="member_not_found",
            )

        member_id = member.id

        self.members.delete(member)

        self.activity.log(
            user_id=actor_id,
            action="member_removed",
            entity_type="project_member",
            entity_id=member_id,
            project_id=project_id,
            old_values={"user_id": target_user_id},
        )

        self.notifications.notify(
            user_id=target_user_id,
            type="project_member_removed",
            title="Доступ к проекту закрыт",
            message=(
                f"Вы больше не участник проекта «{project.name}»"
                if project is not None
                else "Вы больше не участник проекта"
            ),
            project_id=project_id,
            actor_id=actor_id,
        )

        publish(
            project_room(project_id),
            events.MEMBER_REMOVED,
            {
                "project_id": project_id,
                "user_id": target_user_id,
            },
        )

        publish(
            user_room(target_user_id),
            events.MEMBER_REMOVED,
            {
                "project_id": project_id,
            },
        )
