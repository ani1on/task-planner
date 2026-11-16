from sqlalchemy.orm import Session

from ..core.errors import AppException
from ..core.time import utcnow
from ..models.comment import Comment
from ..realtime import events, project_room, publish
from ..repositories.comment import CommentRepository
from ..repositories.task import TaskRepository
from ..schemas.comment import CommentCreate, CommentUpdate
from .access import AccessService
from .activity import ActivityService
from .notification import NotificationService


class CommentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.comments = CommentRepository(db)
        self.tasks = TaskRepository(db)
        self.access = AccessService(db)
        self.activity = ActivityService(db)
        self.notifications = NotificationService(db)

    def list(
        self,
        user_id: int,
        task_id: int | None = None,
    ) -> list[Comment]:
        return self.comments.list_for_user(user_id, task_id)

    def get(
        self,
        comment_id: int,
        user_id: int,
    ) -> Comment:
        comment = self.comments.get_for_user(comment_id, user_id)

        if comment is None:
            raise AppException(
                status_code=404,
                detail="Comment not found",
                code="comment_not_found",
            )

        return comment

    def create(
        self,
        user_id: int,
        data: CommentCreate,
    ) -> Comment:
        task = self.tasks.get_for_user(data.task_id, user_id)

        if task is None:
            raise AppException(
                status_code=404,
                detail="Task not found",
                code="task_not_found",
            )

        comment = Comment(
            task_id=data.task_id,
            author_id=user_id,
            content=data.content,
        )

        self.access.require_role(task.project_id, user_id, "member")

        comment = self.comments.create(comment)

        self.activity.log(
            user_id=user_id,
            action="comment_created",
            entity_type="comment",
            entity_id=comment.id,
            project_id=task.project_id,
            task_id=task.id,
            new_values={"content": comment.content},
        )

        recipients = {
            task.assignee_id,
            task.created_by_id,
        } - {None, user_id}

        for recipient_id in recipients:
            self.notifications.notify(
                user_id=recipient_id,
                type="comment_created",
                title="Новый комментарий",
                message=f"Задача «{task.title}»: {comment.content[:200]}",
                task_id=task.id,
                project_id=task.project_id,
                actor_id=user_id,
            )

        publish(
            project_room(task.project_id),
            events.COMMENT_CREATED,
            {
                "id": comment.id,
                "task_id": task.id,
                "project_id": task.project_id,
                "author_id": comment.author_id,
            },
        )

        return comment

    def update(
        self,
        comment: Comment,
        user_id: int,
        data: CommentUpdate,
    ) -> Comment:
        self.access.require_role(
            comment.task.project_id,
            user_id,
            "member",
        )

        comment.content = data.content

        self.db.flush()

        return comment

    def soft_delete(
        self,
        comment: Comment,
        user_id: int,
    ) -> None:
        self.access.require_role(
            comment.task.project_id,
            user_id,
            "member",
        )

        comment.deleted_at = utcnow()

        self.db.flush()
