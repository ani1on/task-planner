Главная схема
             КОД ПРИЛОЖЕНИЯ
                  │
                  ▼
             FastAPI
                  │
                  ▼
             SQLAlchemy
                  │
          ┌───────┴────────┐
          ▼                ▼
        Base           User model
          │                │
          └───────┬────────┘
                  ▼
               Alembic
                  │
          создаёт migration
                  │
                  ▼
             PostgreSQL
                  │
          ┌───────┴────────┐
          ▼                ▼
        users       alembic_version

Главное правило:

Модель SQLAlchemy описывает, как должна выглядеть БД. Alembic превращает изменение модели в миграцию. PostgreSQL хранит фактическую схему.

1. Что за что отвечает
Компонент	        Задача
FastAPI	API:        принимает запросы от клиента
SQLAlchemy	        Связывает Python-классы с таблицами БД
Base	            Общая база для моделей
Model	            Описание конкретной таблицы
Alembic	            История изменений схемы БД
Migration	        Конкретное изменение БД
PostgreSQL	        Реальная база данных
alembic_version	    Хранит текущую применённую миграцию
2. Где что находится

Пример структуры:

task-planner/
│
├── .env
├── alembic.ini
│
├── alembic/
│   ├── env.py
│   └── versions/
│       ├── 001_create_users.py
│       ├── 002_create_projects.py
│       └── 003_add_task_priority.py
│
└── server/
    ├── main.py
    │
    └── app/
        ├── config.py
        ├── database.py
        │
        └── models/
            ├── __init__.py
            ├── user.py
            ├── project.py
            └── task.py
3. Как создать новую таблицу

Допустим, у нас уже есть:

class User(Base):
    ...

Теперь понадобилась таблица projects.

Создаём:

server/app/models/project.py
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

И добавляем модель в:

server/app/models/__init__.py
from .user import User
from .project import Project

__all__ = ["User", "Project"]
4. После изменения модели

Не надо вручную создавать таблицу в PostgreSQL.

Делаем:

alembic revision --autogenerate -m "create projects table"

Alembic сравнит:

SQLAlchemy models
       │
       │ сравнение
       ▼
текущая схема PostgreSQL

и создаст миграцию.

5. Посмотреть миграцию

После команды:

alembic revision --autogenerate -m "create projects table"

появится:

alembic/
└── versions/
    └── abc123_create_projects_table.py

Всегда полезно открыть этот файл и посмотреть, что Alembic собирается сделать.

Например:

def upgrade():
    op.create_table(
        "projects",
        ...
    )


def downgrade():
    op.drop_table("projects")
6. Применить миграцию
alembic upgrade head

Теперь:

Migration
    │
    ▼
PostgreSQL
    │
    ▼
projects
7. Проверить текущую версию
alembic current

Показать всю историю:

alembic history

Например:

abc123 -> create projects table
def456 -> create tasks table
8. Если сделал несколько миграций

Допустим:

001_create_users
002_create_projects
003_create_tasks
004_add_task_priority

Применить все:

alembic upgrade head

Применить только следующую миграцию:

alembic upgrade +1

Вернуться на одну миграцию назад:

alembic downgrade -1

Вернуться полностью назад:

alembic downgrade base

⚠️ downgrade может удалить таблицы/колонки и данные. Используй осторожно.

9. Изменил существующую модель

Например, было:

class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

Захотели добавить:

description: Mapped[str | None] = mapped_column(
    String(1000),
    nullable=True,
)

Изменяем модель.

Потом:

alembic revision --autogenerate -m "add project description"

Проверяем миграцию.

Потом:

alembic upgrade head

Получаем:

Python Model
     │
     ▼
Alembic migration
     │
     ▼
ALTER TABLE projects
     │
     ▼
PostgreSQL
10. Что НЕЛЬЗЯ делать
❌ Не делать так
Base.metadata.create_all(engine)

для обычной работы проекта с Alembic.

Иначе ты получишь два механизма управления схемой:

create_all()
     +
Alembic

Это приведёт к путанице.

❌ Не редактировать старые применённые миграции

Например, есть:

001_create_users.py

и она уже применена на твоей БД.

Не надо потом менять этот файл.

Вместо этого:

001_create_users
        │
        ▼
002_add_user_avatar
❌ Не удалять миграции просто так

История миграций — часть проекта.

11. Правильный рабочий цикл

Это самая важная часть шпаргалки.

Когда тебе нужно изменить структуру БД:

1. Изменил SQLAlchemy Model
              │
              ▼
2. Проверил модель
              │
              ▼
3. alembic revision --autogenerate
              │
              ▼
4. Проверил созданную migration
              │
              ▼
5. alembic upgrade head
              │
              ▼
6. Проверил PostgreSQL

Запомни:

Сначала Model → потом Migration → потом Database.

Не наоборот.

12. Например, добавляем Tasks

Ты создаёшь:

server/app/models/task.py
class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

Затем:

alembic revision --autogenerate -m "create tasks table"

Проверяешь migration.

Затем:

alembic upgrade head

Получаешь:

PostgreSQL

users
projects
tasks
alembic_version
13. А где здесь FastAPI?

FastAPI не создаёт таблицы.

Например, запрос:

POST /tasks

идёт примерно так:

Desktop Client
      │
      │ HTTP POST /tasks
      ▼
   FastAPI
      │
      ▼
  SQLAlchemy
      │
      ▼
 PostgreSQL

А Alembic в этот момент не участвует.

Alembic нужен для изменения структуры БД:

Developer
    │
    ▼
SQLAlchemy Model
    │
    ▼
Alembic
    │
    ▼
PostgreSQL schema
14. Очень важное различие
Данные

Например:

User:
id = 1
email = "test@example.com"

Создаются через приложение:

FastAPI → SQLAlchemy → PostgreSQL
Структура

Например:

users.email
users.password_hash
users.created_at

Управляется:

SQLAlchemy Model
        ↓
     Alembic
        ↓
   PostgreSQL
15. Команды, которые стоит запомнить
Создать миграцию
alembic revision --autogenerate -m "описание изменения"
Применить миграции
alembic upgrade head
Посмотреть текущую миграцию
alembic current
Посмотреть историю
alembic history
Откатить последнюю
alembic downgrade -1
🧩 Супер-короткая шпаргалка
НУЖНА НОВАЯ ТАБЛИЦА?
        │
        ▼
Создай SQLAlchemy Model
        │
        ▼
Добавь Model в models/__init__.py
        │
        ▼
alembic revision --autogenerate -m "..."
        │
        ▼
ПРОВЕРЬ migration !!!
        │
        ▼
alembic upgrade head
        │
        ▼
Проверь PostgreSQL

И главное правило проекта:

┌─────────────────────────────────────────┐
│ SQLAlchemy Model = желаемая схема       │
│ Alembic Migration = изменение схемы     │
│ PostgreSQL = фактическая схема           │
│ FastAPI = работает с данными             │
└─────────────────────────────────────────┘

Если запомнить только одну последовательность:

Model → revision --autogenerate → проверить migration → upgrade head → PostgreSQL.

Проверка бд:
 docker compose up -d
 docker exec -it task-planner-postgres psql -U task_planner -d task_planner
