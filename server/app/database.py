from collections.abc import Generator
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import settings

engine_kwargs: dict[str, Any] = {
    "echo": settings.app_debug,
    "pool_pre_ping": True,
}

if settings.database_url.startswith("sqlite"):
    # SQLite не поддерживает несколько потоков на одно соединение по умолчанию,
    # а TestClient выполняет запросы в отдельном потоке.
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(
    settings.database_url,
    **engine_kwargs,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
