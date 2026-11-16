"""Преобразование ответов API в модели и словари для UI.

Страницы работают с view-словарями той же структуры, что и
``client/ui/mock_data.py``, поэтому карточки не зависят от источника данных.
"""

from datetime import datetime, timezone
from typing import Any

from .models import (
    Dashboard,
    DashboardStats,
    Member,
    Note,
    Project,
    Tag,
    Task,
    User,
)

MONTHS_GENITIVE = [
    "января",
    "февраля",
    "марта",
    "апреля",
    "мая",
    "июня",
    "июля",
    "августа",
    "сентября",
    "октября",
    "ноября",
    "декабря",
]

WEEKDAYS = [
    "Понедельник",
    "Вторник",
    "Среда",
    "Четверг",
    "Пятница",
    "Суббота",
    "Воскресенье",
]

PREVIEW_LENGTH = 160

ProjectNames = dict[int, str] | None


# ---------------------------------------------------------------------------
# Базовые преобразования
# ---------------------------------------------------------------------------


def _get(data: Any, key: str, default: Any = None) -> Any:
    if isinstance(data, dict):
        return data.get(key, default)

    return getattr(data, key, default)


def parse_datetime(value: Any) -> datetime | None:
    """Разбирает ISO-строку или datetime в локальное время."""
    if value is None or value == "":
        return None

    if isinstance(value, datetime):
        moment = value
    else:
        text = str(value).replace("Z", "+00:00")

        try:
            moment = datetime.fromisoformat(text)
        except ValueError:
            return None

    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)

    return moment.astimezone()


def _now() -> datetime:
    return datetime.now().astimezone()


# ---------------------------------------------------------------------------
# Форматирование дат для интерфейса
# ---------------------------------------------------------------------------


def format_due(value: Any, now: datetime | None = None) -> str:
    """Форматирует дедлайн: «Сегодня, 18:00», «Завтра», «12 октября»."""
    moment = parse_datetime(value)

    if moment is None:
        return ""

    now = now or _now()
    days = (moment.date() - now.date()).days

    if days == 0:
        return f"Сегодня, {moment:%H:%M}"

    if days == 1:
        return "Завтра"

    if days == -1:
        return "Вчера"

    if 1 < days < 7:
        return WEEKDAYS[moment.weekday()]

    if moment.year == now.year:
        return f"{moment.day} {MONTHS_GENITIVE[moment.month - 1]}"

    return f"{moment.day} {MONTHS_GENITIVE[moment.month - 1]} {moment.year}"


def format_relative(value: Any, now: datetime | None = None) -> str:
    """Форматирует «2 часа назад» / «Вчера» для заметок."""
    moment = parse_datetime(value)

    if moment is None:
        return ""

    now = now or _now()
    seconds = (now - moment).total_seconds()

    if seconds < 60:
        return "Только что"

    if seconds < 3600:
        return f"{int(seconds // 60)} мин назад"

    if seconds < 86400:
        return f"{int(seconds // 3600)} ч назад"

    days = (now.date() - moment.date()).days

    if days == 1:
        return "Вчера"

    if days < 7:
        return f"{days} дн назад"

    if moment.year == now.year:
        return f"{moment.day} {MONTHS_GENITIVE[moment.month - 1]}"

    return f"{moment.day} {MONTHS_GENITIVE[moment.month - 1]} {moment.year}"


def preview_text(text: str, length: int = PREVIEW_LENGTH) -> str:
    """Схлопывает пробелы и обрезает текст заметки."""
    collapsed = " ".join((text or "").split())

    if len(collapsed) <= length:
        return collapsed

    return collapsed[: length - 1].rstrip() + "…"


# ---------------------------------------------------------------------------
# JSON -> модели
# ---------------------------------------------------------------------------


def user_from_dict(data: dict[str, Any]) -> User:
    return User(
        id=_get(data, "id", 0),
        email=_get(data, "email", ""),
        nick_name=_get(data, "nick_name", ""),
        avatar_url=_get(data, "avatar_url", "") or "",
        email_verified=bool(_get(data, "email_verified", False)),
    )


def tag_from_dict(data: dict[str, Any]) -> Tag:
    return Tag(
        id=_get(data, "id", 0),
        project_id=_get(data, "project_id", 0),
        name=_get(data, "name", ""),
        color=_get(data, "color", "blue"),
        created_at=parse_datetime(_get(data, "created_at")),
        updated_at=parse_datetime(_get(data, "updated_at")),
    )


def task_from_dict(data: dict[str, Any]) -> Task:
    return Task(
        id=_get(data, "id", 0),
        project_id=_get(data, "project_id", 0),
        title=_get(data, "title", ""),
        status=_get(data, "status", "todo"),
        priority=_get(data, "priority", "medium"),
        description=_get(data, "description"),
        parent_task_id=_get(data, "parent_task_id"),
        assignee_id=_get(data, "assignee_id"),
        created_by_id=_get(data, "created_by_id"),
        position=_get(data, "position", 0) or 0,
        start_at=parse_datetime(_get(data, "start_at")),
        due_at=parse_datetime(_get(data, "due_at")),
        completed_at=parse_datetime(_get(data, "completed_at")),
        created_at=parse_datetime(_get(data, "created_at")),
        updated_at=parse_datetime(_get(data, "updated_at")),
        tags=tuple(tag_from_dict(tag) for tag in _get(data, "tags", []) or []),
    )


def project_from_dict(data: dict[str, Any]) -> Project:
    return Project(
        id=_get(data, "id", 0),
        name=_get(data, "name", ""),
        description=_get(data, "description"),
        color=_get(data, "color", "blue"),
        status=_get(data, "status", "active"),
        owner_id=_get(data, "owner_id"),
        role=_get(data, "role"),
        progress=_get(data, "progress", 0) or 0,
        tasks_total=_get(data, "tasks_total", 0) or 0,
        tasks_done=_get(data, "tasks_done", 0) or 0,
        created_at=parse_datetime(_get(data, "created_at")),
        updated_at=parse_datetime(_get(data, "updated_at")),
    )


def member_from_dict(data: dict[str, Any]) -> Member:
    user = _get(data, "user", {}) or {}

    return Member(
        id=_get(data, "id", 0),
        project_id=_get(data, "project_id", 0),
        user_id=_get(data, "user_id", 0),
        role=_get(data, "role", "member"),
        nick_name=_get(user, "nick_name", ""),
        email=_get(user, "email", ""),
        avatar_url=_get(user, "avatar_url", "") or "",
        joined_at=parse_datetime(_get(data, "joined_at")),
    )


def note_from_dict(data: dict[str, Any]) -> Note:
    return Note(
        id=_get(data, "id", 0),
        title=_get(data, "title", ""),
        content=_get(data, "content", ""),
        project_id=_get(data, "project_id"),
        task_id=_get(data, "task_id"),
        user_id=_get(data, "user_id"),
        is_pinned=bool(_get(data, "is_pinned", False)),
        created_at=parse_datetime(_get(data, "created_at")),
        updated_at=parse_datetime(_get(data, "updated_at")),
    )


def stats_from_dict(data: dict[str, Any]) -> DashboardStats:
    return DashboardStats(
        total=_get(data, "total", 0) or 0,
        todo=_get(data, "todo", 0) or 0,
        in_progress=_get(data, "in_progress", 0) or 0,
        review=_get(data, "review", 0) or 0,
        done=_get(data, "done", 0) or 0,
        overdue=_get(data, "overdue", 0) or 0,
        due_today=_get(data, "due_today", 0) or 0,
    )


def dashboard_from_dict(data: dict[str, Any]) -> Dashboard:
    return Dashboard(
        stats=stats_from_dict(_get(data, "stats", {}) or {}),
        projects=tuple(
            project_from_dict(item) for item in _get(data, "projects", []) or []
        ),
        recent_projects=tuple(
            project_from_dict(item)
            for item in _get(data, "recent_projects", []) or []
        ),
        upcoming_tasks=tuple(
            task_from_dict(item) for item in _get(data, "upcoming_tasks", []) or []
        ),
        recent_tasks=tuple(
            task_from_dict(item) for item in _get(data, "recent_tasks", []) or []
        ),
        total_projects=_get(data, "total_projects", 0) or 0,
    )


# ---------------------------------------------------------------------------
# модели -> view-словари для UI
# ---------------------------------------------------------------------------


def task_view(task: Task, project_names: ProjectNames = None) -> dict[str, Any]:
    names = project_names or {}

    return {
        "id": task.id,
        "title": task.title,
        "project": names.get(task.project_id),
        "status": task.status,
        "priority": task.priority,
        "due": format_due(task.due_at),
        "due_at": task.due_at,
        "tags": [tag.name for tag in task.tags],
        "done": task.is_done,
    }


def project_view(
    project: Project,
    members: list[Member] | tuple[Member, ...] = (),
) -> dict[str, Any]:
    return {
        "id": project.id,
        "name": project.name,
        "description": project.description or "",
        "color": project.color,
        "status": project.status,
        "done": project.tasks_done,
        "total": project.tasks_total,
        "progress": project.percent,
        "role": project.role,
        "members": [member.nick_name for member in members],
    }


def note_view(note: Note, project_names: ProjectNames = None) -> dict[str, Any]:
    names = project_names or {}

    return {
        "id": note.id,
        "title": note.title,
        "preview": preview_text(note.content),
        "project": names.get(note.project_id) if note.project_id else None,
        "updated": format_relative(note.updated_at or note.created_at),
        "is_pinned": note.is_pinned,
    }


def dashboard_stats_view(stats: DashboardStats) -> list[dict[str, str]]:
    return [
        {"label": "Всего задач", "value": str(stats.total), "accent": "primary"},
        {"label": "В работе", "value": str(stats.in_progress), "accent": "warning"},
        {"label": "Выполнено", "value": str(stats.done), "accent": "success"},
        {"label": "Просрочено", "value": str(stats.overdue), "accent": "danger"},
    ]


