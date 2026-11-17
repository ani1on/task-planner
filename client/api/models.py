"""Модели данных, которые клиент получает от backend.

Модели повторяют ответы API (см. server/app/schemas) и не зависят от UI.
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class User:
    id: int
    email: str
    nick_name: str
    avatar_url: str = ""
    email_verified: bool = False


@dataclass(frozen=True)
class Tag:
    id: int
    project_id: int
    name: str
    color: str = "blue"
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class Task:
    id: int
    project_id: int
    title: str
    status: str = "todo"
    priority: str = "medium"
    description: str | None = None
    parent_task_id: int | None = None
    assignee_id: int | None = None
    created_by_id: int | None = None
    position: int = 0
    start_at: datetime | None = None
    due_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    tags: tuple[Tag, ...] = field(default_factory=tuple)

    @property
    def is_done(self) -> bool:
        return self.status == "done" or self.completed_at is not None


@dataclass(frozen=True)
class Project:
    id: int
    name: str
    description: str | None = None
    color: str = "blue"
    status: str = "active"
    owner_id: int | None = None
    role: str | None = None
    progress: int = 0
    tasks_total: int = 0
    tasks_done: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def percent(self) -> int:
        if self.progress:
            return self.progress
        if self.tasks_total:
            return int(self.tasks_done / self.tasks_total * 100)
        return 0


@dataclass(frozen=True)
class Member:
    id: int
    project_id: int
    user_id: int
    role: str
    nick_name: str
    email: str = ""
    avatar_url: str = ""
    joined_at: datetime | None = None


@dataclass(frozen=True)
class Note:
    id: int
    title: str
    content: str
    project_id: int | None = None
    task_id: int | None = None
    user_id: int | None = None
    is_pinned: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class Comment:
    id: int
    task_id: int
    author_id: int
    content: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class ChecklistItem:
    id: int
    checklist_id: int
    content: str
    is_completed: bool = False
    position: int = 0


@dataclass(frozen=True)
class Checklist:
    id: int
    task_id: int
    title: str
    position: int = 0
    items: tuple[ChecklistItem, ...] = field(default_factory=tuple)

    @property
    def completed(self) -> int:
        return sum(1 for item in self.items if item.is_completed)


@dataclass(frozen=True)
class Notification:
    id: int
    title: str
    text: str = ""
    is_read: bool = False
    created_at: datetime | None = None


@dataclass(frozen=True)
class Event:
    id: int
    title: str
    start_at: datetime
    end_at: datetime
    description: str | None = None
    project_id: int | None = None
    task_id: int | None = None
    all_day: bool = False
    location: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class Reminder:
    id: int
    remind_at: datetime
    channel: str
    status: str
    task_id: int | None = None
    event_id: int | None = None
    sent_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class Recurrence:
    id: int
    task_id: int
    frequency: str
    interval: int
    start_at: datetime
    is_active: bool = True
    days_of_week: tuple[int, ...] | None = None
    day_of_month: int | None = None
    end_at: datetime | None = None
    next_run_at: datetime | None = None


@dataclass(frozen=True)
class Activity:
    id: int
    action: str
    entity_type: str
    entity_id: int
    user_id: int | None = None
    project_id: int | None = None
    task_id: int | None = None
    old_values: dict | None = None
    new_values: dict | None = None
    created_at: datetime | None = None


@dataclass(frozen=True)
class DashboardStats:
    total: int = 0
    todo: int = 0
    in_progress: int = 0
    review: int = 0
    done: int = 0
    overdue: int = 0
    due_today: int = 0


@dataclass(frozen=True)
class Dashboard:
    stats: DashboardStats
    projects: tuple[Project, ...] = field(default_factory=tuple)
    recent_projects: tuple[Project, ...] = field(default_factory=tuple)
    upcoming_tasks: tuple[Task, ...] = field(default_factory=tuple)
    recent_tasks: tuple[Task, ...] = field(default_factory=tuple)
    total_projects: int = 0
