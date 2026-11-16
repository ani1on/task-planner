import os
import tempfile
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Тесты должны работать без запущенного PostgreSQL, поэтому до импорта
# приложения переключаем настройки на временную SQLite-базу.
_TEST_DB_DIR = Path(tempfile.mkdtemp(prefix="task_planner_tests_"))
_TEST_DB_PATH = _TEST_DB_DIR / "test.db"

os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB_PATH.as_posix()}"
os.environ["APP_DEBUG"] = "false"
os.environ["RATE_LIMIT_ENABLED"] = "false"
os.environ["REMINDERS_WORKER_ENABLED"] = "false"

from server.app import models  # noqa: F401
from server.app.core.ratelimit import reset_limiter
from server.app.database import Base, engine
from server.main import app


@pytest.fixture(scope="session", autouse=True)
def _database() -> None:
    Base.metadata.create_all(bind=engine)

    yield

    Base.metadata.drop_all(bind=engine)
    engine.dispose()

    try:
        _TEST_DB_PATH.unlink(missing_ok=True)
        _TEST_DB_DIR.rmdir()
    except OSError:
        pass


@pytest.fixture(autouse=True)
def _reset_rate_limit() -> None:
    reset_limiter()


def make_user() -> tuple[str, str, str]:
    suffix = uuid.uuid4().hex[:12]

    return (
        f"test_{suffix}@example.com",
        f"test_{suffix}",
        "test_password_123",
    )


def authenticated_client() -> TestClient:
    client = TestClient(app)

    email, nick_name, password = make_user()

    response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
            "nick_name": nick_name,
        },
    )

    assert response.status_code == 201, response.text

    response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 200, response.text

    token = response.json()["access_token"]

    client.headers.update({"Authorization": f"Bearer {token}"})

    return client


@pytest.fixture()
def auth_client() -> TestClient:
    return authenticated_client()


@pytest.fixture()
def other_client() -> TestClient:
    return authenticated_client()
