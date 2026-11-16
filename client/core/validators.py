"""Общие проверки данных форм."""

import re

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

MIN_PASSWORD_LENGTH = 8

MIN_NICKNAME_LENGTH = 2


def is_valid_email(value: str) -> bool:
    return bool(EMAIL_RE.match((value or "").strip()))
