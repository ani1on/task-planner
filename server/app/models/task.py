from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from .checklist import Checklist
    from .comment import Comment
    from .project import Project
    from .task_recurrence import TaskRecurrence
    from .task_tag import TaskTag
    from .user import User


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    parent_task_id: Mapped[int | None] = mapped_column(
        ForeignKey("tasks.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    assignee_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    created_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        server_default="todo",
        index=True,
    )

    priority: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="medium",
        index=True,
    )

    position: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="0",
    )

    start_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    due_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
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

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="tasks",
    )

    parent_task: Mapped["Task | None"] = relationship(
        "Task",
        remote_side=[id],
        back_populates="subtasks",
    )

    subtasks: Mapped[list["Task"]] = relationship(
        "Task",
        back_populates="parent_task",
    )

    assignee: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[assignee_id],
    )

    created_by: Mapped["User"] = relationship(
        "User",
        foreign_keys=[created_by_id],
    )

    recurrence: Mapped["TaskRecurrence | None"] = relationship(
        "TaskRecurrence",
        back_populates="task",
        uselist=False,
        cascade="all, delete-orphan",
    )

    checklists: Mapped[list["Checklist"]] = relationship(
        "Checklist",
        back_populates="task",
        cascade="all, delete-orphan",
    )

    comments: Mapped[list["Comment"]] = relationship(
        "Comment",
        back_populates="task",
    )

    task_tags: Mapped[list["TaskTag"]] = relationship(
        "TaskTag",
        back_populates="task",
        cascade="all, delete-orphan",
    )
