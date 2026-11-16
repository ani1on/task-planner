from datetime import date, datetime, time
from enum import Enum
from typing import Any


def jsonable(value: Any) -> Any:
    """Преобразует значение в структуру, пригодную для JSON-колонки."""
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()

    if isinstance(value, Enum):
        return value.value

    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}

    if isinstance(value, (list, tuple, set)):
        return [jsonable(item) for item in value]

    if isinstance(value, (str, int, float, bool)) or value is None:
        return value

    return str(value)
