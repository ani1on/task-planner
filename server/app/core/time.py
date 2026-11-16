from datetime import datetime, timezone


def utcnow() -> datetime:
    """Текущее время в UTC с таймзоной."""
    return datetime.now(timezone.utc)


def ensure_utc(value: datetime) -> datetime:
    """Приводит datetime к aware-UTC.

    Нужно для баз данных, которые возвращают naive datetime
    (например, SQLite в тестах).
    """
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)
