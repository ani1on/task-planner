# Task Planner

> Полнофункциональное приложение для управления задачами с десктопным клиентом, REST API и поддержкой реального времени.

## 📋 Обзор

Task Planner — это комплексная система управления проектами, построенная на современной архитектуре:

- **Десктопный клиент**: PySide6 (Qt для Python) — кроссплатформенное приложение
- **Backend API**: FastAPI — высокопроизводительный REST API с поддержкой WebSocket
- **База данных**: PostgreSQL — надёжная реляционная СУБД в Docker

Приложение поддерживает как **локальную разработку**, так и **продакшн-развёртывание** с плавным переходом от локального тестирования к облачной многопользовательской работе.

---

## 🚀 Ключевые возможности

### Управление задачами
- Создание, редактирование, удаление и выполнение задач
- Статусы задач (К выполнению, В работе, Готово и др.)
- Приоритеты (Низкий, Средний, Высокий, Критический)
- Даты начала, дедлайны и учёт времени
- Описания и метаданные задач
- Подзадачи с отслеживанием прогресса
- Повторяющиеся задачи (ежедневно, еженедельно, ежемесячно)

### Организация проектов
- Создание и управление проектами
- Участники проектов с правами доступа
- Отслеживание прогресса проекта
- Цветовая маркировка и архивация
- Настройки проекта

### Совместная работа
- Многопользовательский режим с аутентификацией
- Приглашения участников и управление командой
- Назначение задач и делегирование
- Обновления в реальном времени через WebSocket

### Инструменты продуктивности
- **Чек-листы**: создание и отслеживание прогресса
- **Теги**: категоризация задач
- **Комментарии**: обсуждение задач в команде
- **Заметки**: хранение информации по проектам
- **Канбан-доска**: визуальное управление задачами с Drag & Drop
- **Календарь**: просмотр задач и дедлайнов

### Уведомления и напоминания
- Внутренние уведомления в приложении
- Уведомления о назначении задач
- Уведомления о комментариях
- Приглашения в проекты
- Десктопные напоминания о дедлайнах

### Пользовательский опыт
- Светлая и тёмная темы
- Боковая панель с навигацией
- Поиск по всем разделам
- Расширенная фильтрация (по статусу, приоритету, исполнителю, тегам, датам)
- Дашборд со сводной статистикой
- Профиль пользователя с аватаром и настройками

---

## 🏗️ Архитектура

### Локальная разработка
```
┌───────────────────────────────────────┐
│              ВАШ ПК                   │
│                                       │
│  ┌───────────────┐                    │
│  │   PySide6     │  Десктопный клиент │
│  └───────┬───────┘                    │
│          │                             │
│          ▼                             │
│  ┌───────────────┐                    │
│  │    FastAPI    │  Backend API       │
│  └───────┬───────┘                    │
│          │                             │
│          ▼                             │
│  ┌───────────────┐                    │
│  │  PostgreSQL   │  База данных       │
│  │    Docker     │                    │
│  └───────────────┘                    │
│                                       │
└───────────────────────────────────────┘
```

### Продакшн-развёртывание
```
           ИНТЕРНЕТ
              │
     ┌────────┴────────┐
     │                 │
 Desktop A         Desktop B
     │                 │
     └────────┬────────┘
              │
           HTTPS/WSS
              │
              ▼
     ┌─────────────────┐
     │   VPS / Cloud   │
     │                 │
     │  ┌───────────┐  │
     │  │  FastAPI  │  │
     │  └─────┬─────┘  │
     │        │        │
     │  ┌─────▼─────┐  │
     │  │PostgreSQL │  │
     │  └───────────┘  │
     └─────────────────┘
```

---

## 🔌 Backend API

Все маршруты (кроме `/health` и `/auth/*`) требуют заголовок
`Authorization: Bearer <access_token>`.

| Группа | Маршруты |
| --- | --- |
| Auth | `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`, `POST /auth/logout`, `GET /auth/me`, `POST /auth/change-password`, `POST /auth/forgot-password`, `POST /auth/reset-password` |
| Projects | `GET/POST /projects`, `GET/PATCH/DELETE /projects/{id}`, `POST /projects/{id}/archive`, `GET /projects/{id}/progress` |
| Members | `GET/POST /projects/{id}/members`, `PATCH/DELETE /projects/{id}/members/{user_id}` |
| Tasks | `GET/POST /tasks`, `GET/PATCH/DELETE /tasks/{id}`, `GET/POST /tasks/{id}/subtasks`, `GET /tasks/{id}/subtasks/progress` |
| Task tags | `GET /tasks/{id}/tags`, `POST/DELETE /tasks/{id}/tags/{tag_id}` |
| Recurrence | `GET/PUT/PATCH/DELETE /tasks/{id}/recurrence`, `POST /tasks/{id}/next-occurrence` |
| Tags | `GET/POST /tags`, `GET/PATCH/DELETE /tags/{id}` |
| Checklists | `GET/POST /checklists`, `GET/PATCH/DELETE /checklists/{id}`, `GET/POST /checklists/{id}/items`, `PATCH/DELETE /checklist-items/{id}` |
| Comments | `GET/POST /comments`, `GET/PATCH/DELETE /comments/{id}` |
| Notes | `GET/POST /notes`, `GET/PATCH/DELETE /notes/{id}` |
| Events | `GET/POST /events`, `GET/PATCH/DELETE /events/{id}` |
| Reminders | `GET/POST /reminders`, `GET/PATCH/DELETE /reminders/{id}`, `POST /reminders/process-due` |
| Notifications | `GET /notifications`, `GET /notifications/unread-count`, `POST /notifications/{id}/read`, `POST /notifications/read-all` |
| Activity | `GET /activity?project_id=&task_id=` |
| Dashboard | `GET /dashboard` |
| Search | `GET /search?q=` |
| Profile | `GET/PATCH /users/me`, `GET/PATCH /users/me/settings` |
| Health | `GET /health`, `GET /health/db` |
| Realtime | `WS /ws?token=<access_token>` |

### Права доступа

В проекте четыре роли: `owner`, `admin`, `member`, `viewer`.
Просмотр доступен всем участникам, изменение задач — `member` и выше,
управление участниками — `admin` и `owner`. Доступ к проектам и задачам
проверяется через `project_members`, поэтому чужие данные возвращают `404`.

### WebSocket

Клиент подключается к `/ws?token=<access_token>` и может отправлять команды:

```json
{"action": "ping"}
{"action": "join_project", "project_id": 1}
{"action": "leave_project", "project_id": 1}
```

События проекта (`task_created`, `task_updated`, `task_deleted`, `task_assigned`,
`comment_created`, `member_added`, `member_removed`, `project_updated`) приходят
в комнату `project:{id}`, уведомления и напоминания — в комнату `user:{id}`.

### Напоминания

Напоминания можно обрабатывать вручную (`POST /reminders/process-due`) или
фоновым воркером: `REMINDERS_WORKER_ENABLED=True` в `.env`.

### Защита dev-маршрутов

Маршруты `/dev/*` подключаются только когда `APP_ENV != production`.
В production они недоступны.

---

## 🧪 Тесты и линтеры

```powershell
.\venv\Scripts\python.exe -m pytest
.\venv\Scripts\python.exe -m ruff check .
```

Тесты используют изолированную SQLite-базу во временном каталоге
(`server/tests/conftest.py`), поэтому запущенный PostgreSQL и Docker не нужны.
