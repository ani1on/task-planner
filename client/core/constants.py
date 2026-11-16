"""Общие константы клиента.

Строковые значения статусов и приоритетов совпадают со значениями,
которые backend хранит в БД (см. server/app/models/task.py).
"""

STATUS_TODO = "todo"
STATUS_IN_PROGRESS = "in_progress"
STATUS_REVIEW = "review"
STATUS_DONE = "done"

TASK_STATUSES = [
    STATUS_TODO,
    STATUS_IN_PROGRESS,
    STATUS_REVIEW,
    STATUS_DONE,
]

STATUS_LABELS = {
    STATUS_TODO: "К выполнению",
    STATUS_IN_PROGRESS: "В работе",
    STATUS_REVIEW: "На проверке",
    STATUS_DONE: "Готово",
}

STATUS_BADGES = {
    STATUS_TODO: "neutral",
    STATUS_IN_PROGRESS: "primary",
    STATUS_REVIEW: "warning",
    STATUS_DONE: "success",
}

PRIORITY_LOW = "low"
PRIORITY_MEDIUM = "medium"
PRIORITY_HIGH = "high"
PRIORITY_CRITICAL = "critical"

TASK_PRIORITIES = [
    PRIORITY_LOW,
    PRIORITY_MEDIUM,
    PRIORITY_HIGH,
    PRIORITY_CRITICAL,
]

PRIORITY_LABELS = {
    PRIORITY_LOW: "Низкий",
    PRIORITY_MEDIUM: "Средний",
    PRIORITY_HIGH: "Высокий",
    PRIORITY_CRITICAL: "Критический",
}

PRIORITY_BADGES = {
    PRIORITY_LOW: "neutral",
    PRIORITY_MEDIUM: "primary",
    PRIORITY_HIGH: "warning",
    PRIORITY_CRITICAL: "danger",
}

PROJECT_STATUS_ACTIVE = "active"
PROJECT_STATUS_ARCHIVED = "archived"

PROJECT_STATUS_LABELS = {
    PROJECT_STATUS_ACTIVE: "Активный",
    PROJECT_STATUS_ARCHIVED: "В архиве",
}

PROJECT_COLORS = {
    "blue": "#2563eb",
    "green": "#16a34a",
    "purple": "#7c3aed",
    "orange": "#ea580c",
    "red": "#dc2626",
    "teal": "#0d9488",
}

PROJECT_COLOR_LABELS = {
    "blue": "Синий",
    "green": "Зелёный",
    "purple": "Фиолетовый",
    "orange": "Оранжевый",
    "red": "Красный",
    "teal": "Бирюзовый",
}
