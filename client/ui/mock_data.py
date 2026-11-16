"""Временные данные для каркаса интерфейса.

Пока backend не отдаёт projects/tasks/notes, страницы наполняются
этими словарями. Структура совпадает с будущими ответами API,
поэтому при подключении реальных запросов страницы менять не придётся.
"""

from client.core.constants import (
    PRIORITY_CRITICAL,
    PRIORITY_HIGH,
    PRIORITY_LOW,
    PRIORITY_MEDIUM,
    PROJECT_STATUS_ACTIVE,
    STATUS_DONE,
    STATUS_IN_PROGRESS,
    STATUS_REVIEW,
    STATUS_TODO,
)


def current_user() -> dict:
    return {
        "id": 1,
        "nick_name": "Анна Смирнова",
        "email": "anna@example.com",
    }


def dashboard_stats() -> list[dict]:
    return [
        {"label": "Всего задач", "value": "128", "accent": "primary"},
        {"label": "В работе", "value": "17", "accent": "warning"},
        {"label": "Выполнено", "value": "96", "accent": "success"},
        {"label": "Просрочено", "value": "4", "accent": "danger"},
    ]


def tasks() -> list[dict]:
    return [
        {
            "id": 1,
            "title": "Собрать каркас интерфейса",
            "project": "Task Planner",
            "status": STATUS_IN_PROGRESS,
            "priority": PRIORITY_HIGH,
            "due": "Сегодня, 18:00",
            "tags": ["ui", "frontend"],
            "done": False,
        },
        {
            "id": 2,
            "title": "Продумать схему базы данных",
            "project": "Task Planner",
            "status": STATUS_DONE,
            "priority": PRIORITY_MEDIUM,
            "due": "Вчера",
            "tags": ["backend", "db"],
            "done": True,
        },
        {
            "id": 3,
            "title": "Подключить авторизацию",
            "project": "Task Planner",
            "status": STATUS_REVIEW,
            "priority": PRIORITY_CRITICAL,
            "due": "Завтра",
            "tags": ["auth"],
            "done": False,
        },
        {
            "id": 4,
            "title": "Описать REST API задач",
            "project": "Документация",
            "status": STATUS_TODO,
            "priority": PRIORITY_LOW,
            "due": "12 октября",
            "tags": ["docs"],
            "done": False,
        },
        {
            "id": 5,
            "title": "Настроить CI для тестов",
            "project": "Инфраструктура",
            "status": STATUS_TODO,
            "priority": PRIORITY_MEDIUM,
            "due": "15 октября",
            "tags": ["ci"],
            "done": False,
        },
    ]


def kanban_columns() -> list[dict]:
    all_tasks = tasks()

    return [
        {
            "key": STATUS_TODO,
            "title": "К выполнению",
            "tasks": [t for t in all_tasks if t["status"] == STATUS_TODO],
        },
        {
            "key": STATUS_IN_PROGRESS,
            "title": "В работе",
            "tasks": [t for t in all_tasks if t["status"] == STATUS_IN_PROGRESS],
        },
        {
            "key": STATUS_REVIEW,
            "title": "На проверке",
            "tasks": [t for t in all_tasks if t["status"] == STATUS_REVIEW],
        },
        {
            "key": STATUS_DONE,
            "title": "Готово",
            "tasks": [t for t in all_tasks if t["status"] == STATUS_DONE],
        },
    ]


def projects() -> list[dict]:
    return [
        {
            "id": 1,
            "name": "Task Planner",
            "description": "Десктопный планировщик задач на PySide6 и FastAPI.",
            "color": "blue",
            "status": PROJECT_STATUS_ACTIVE,
            "done": 96,
            "total": 128,
            "members": ["Анна Смирнова", "Игорь Петров", "Мария Ли"],
        },
        {
            "id": 2,
            "name": "Документация",
            "description": "Описание API, схемы данных и руководство пользователя.",
            "color": "purple",
            "status": PROJECT_STATUS_ACTIVE,
            "done": 12,
            "total": 30,
            "members": ["Анна Смирнова", "Мария Ли"],
        },
        {
            "id": 3,
            "name": "Инфраструктура",
            "description": "Docker, миграции, CI/CD и подготовка к продакшену.",
            "color": "teal",
            "status": PROJECT_STATUS_ACTIVE,
            "done": 8,
            "total": 24,
            "members": ["Игорь Петров"],
        },
        {
            "id": 4,
            "name": "Мобильный клиент",
            "description": "Идея на будущее: клиент для телефона.",
            "color": "orange",
            "status": "archived",
            "done": 0,
            "total": 0,
            "members": ["Анна Смирнова"],
        },
    ]


def notes() -> list[dict]:
    return [
        {
            "id": 1,
            "title": "Идеи по дизайну",
            "preview": "Тёмная тема должна быть мягкой, без чистого чёрного. "
            "Использовать акцентный синий для активных элементов.",
            "project": "Task Planner",
            "updated": "2 часа назад",
        },
        {
            "id": 2,
            "title": "Список эндпоинтов",
            "preview": "GET /tasks, POST /tasks, PATCH /tasks/{id}, "
            "GET /projects, POST /projects ...",
            "project": "Документация",
            "updated": "Вчера",
        },
        {
            "id": 3,
            "title": "План на неделю",
            "preview": "Понедельник — каркас UI. Вторник — API проектов. "
            "Среда — API задач. Четверг — канбан.",
            "project": "Task Planner",
            "updated": "3 дня назад",
        },
        {
            "id": 4,
            "title": "Вопросы к заказчику",
            "preview": "Нужны ли роли в проектах на первом этапе? "
            "Делать ли гостевой доступ?",
            "project": None,
            "updated": "Неделю назад",
        },
    ]


def upcoming_events() -> list[dict]:
    return [
        {"day": 2, "title": "Демо каркаса"},
        {"day": 5, "title": "Дедлайн API"},
        {"day": 5, "title": "Ревью"},
        {"day": 9, "title": "Созвон команды"},
        {"day": 14, "title": "Релиз 0.1"},
        {"day": 21, "title": "Планирование"},
    ]


def notifications() -> list[dict]:
    return [
        {
            "id": 1,
            "title": "Вам назначена задача",
            "text": "Собрать каркас интерфейса",
            "time": "10 минут назад",
            "unread": True,
        },
        {
            "id": 2,
            "title": "Новый комментарий",
            "text": "Игорь Петров в задаче «Подключить авторизацию»",
            "time": "1 час назад",
            "unread": True,
        },
        {
            "id": 3,
            "title": "Дедлайн приближается",
            "text": "Задача «Описать REST API задач» — 12 октября",
            "time": "Вчера",
            "unread": False,
        },
    ]
