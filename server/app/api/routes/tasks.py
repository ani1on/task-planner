from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ...api.deps import get_current_user
from ...api.serializers import task_response
from ...core.errors import AppException
from ...database import get_db
from ...models.user import User
from ...schemas.common import MessageResponse
from ...schemas.recurrence import (
    RecurrenceCreate,
    RecurrenceResponse,
    RecurrenceUpdate,
)
from ...schemas.tag import TagResponse
from ...schemas.task import (
    SubtaskCreate,
    SubtaskProgress,
    TaskCreate,
    TaskResponse,
    TaskUpdate,
)
from ...services.recurrence import RecurrenceService
from ...services.task import TaskService

router = APIRouter(
    prefix="/tasks",
    tags=["Tasks"],
)


@router.get(
    "",
    response_model=list[TaskResponse],
)
def list_tasks(
    project_id: int | None = None,
    status_filter: str | None = None,
    priority: str | None = None,
    assignee_id: int | None = None,
    tag_id: int | None = None,
    search: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[TaskResponse]:
    service = TaskService(db)

    tasks = service.list(
        user_id=current_user.id,
        project_id=project_id,
        status=status_filter,
        priority=priority,
        assignee_id=assignee_id,
        tag_id=tag_id,
        search=search,
    )

    return [task_response(task) for task in tasks]


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
)
def get_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskResponse:
    service = TaskService(db)

    task = service.get(task_id, current_user.id)

    return task_response(task)


@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_task(
    data: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskResponse:
    service = TaskService(db)

    task = service.create(current_user.id, data)

    db.commit()

    return task_response(task)


@router.patch(
    "/{task_id}",
    response_model=TaskResponse,
)
def update_task(
    task_id: int,
    data: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskResponse:
    service = TaskService(db)

    task = service.get(task_id, current_user.id)
    task = service.update(task, current_user.id, data)

    db.commit()

    return task_response(task)


@router.delete(
    "/{task_id}",
    response_model=MessageResponse,
)
def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    service = TaskService(db)

    task = service.get(task_id, current_user.id)

    service.soft_delete(task, current_user.id)

    db.commit()

    return MessageResponse(message="Task deleted")


# ---------------------------------------------------------------------------
# Подзадачи
# ---------------------------------------------------------------------------


@router.get(
    "/{task_id}/subtasks",
    response_model=list[TaskResponse],
)
def list_subtasks(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[TaskResponse]:
    service = TaskService(db)

    task = service.get(task_id, current_user.id)

    return [
        task_response(subtask)
        for subtask in service.list_subtasks(task)
    ]


@router.get(
    "/{task_id}/subtasks/progress",
    response_model=SubtaskProgress,
)
def get_subtask_progress(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SubtaskProgress:
    service = TaskService(db)

    task = service.get(task_id, current_user.id)
    total, completed = service.subtask_progress(task)

    return SubtaskProgress(total=total, completed=completed)


@router.post(
    "/{task_id}/subtasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_subtask(
    task_id: int,
    data: SubtaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskResponse:
    service = TaskService(db)

    parent = service.get(task_id, current_user.id)
    subtask = service.create_subtask(parent, current_user.id, data)

    db.commit()

    return task_response(subtask)


# ---------------------------------------------------------------------------
# Теги задачи
# ---------------------------------------------------------------------------


@router.get(
    "/{task_id}/tags",
    response_model=list[TagResponse],
)
def list_task_tags(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[TagResponse]:
    service = TaskService(db)

    task = service.get(task_id, current_user.id)

    return [
        TagResponse.model_validate(tag)
        for tag in service.list_tags(task)
    ]


@router.post(
    "/{task_id}/tags/{tag_id}",
    response_model=list[TagResponse],
)
def add_task_tag(
    task_id: int,
    tag_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[TagResponse]:
    service = TaskService(db)

    task = service.get(task_id, current_user.id)
    service.add_tag(task, tag_id, current_user.id)

    db.commit()

    return [
        TagResponse.model_validate(tag)
        for tag in service.list_tags(task)
    ]


@router.delete(
    "/{task_id}/tags/{tag_id}",
    response_model=MessageResponse,
)
def remove_task_tag(
    task_id: int,
    tag_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    service = TaskService(db)

    task = service.get(task_id, current_user.id)
    service.remove_tag(task, tag_id)

    db.commit()

    return MessageResponse(message="Tag removed from task")


# ---------------------------------------------------------------------------
# Повторяющиеся задачи
# ---------------------------------------------------------------------------


@router.get(
    "/{task_id}/recurrence",
    response_model=RecurrenceResponse,
)
def get_task_recurrence(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RecurrenceResponse:
    service = TaskService(db)

    task = service.get(task_id, current_user.id)
    recurrence = service.recurrences.get(task)

    if recurrence is None:
        raise AppException(
            status_code=404,
            detail="Task recurrence not found",
            code="recurrence_not_found",
        )

    return RecurrenceResponse.model_validate(recurrence)


@router.put(
    "/{task_id}/recurrence",
    response_model=RecurrenceResponse,
)
def set_task_recurrence(
    task_id: int,
    data: RecurrenceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RecurrenceResponse:
    service = TaskService(db)

    task = service.get(task_id, current_user.id)
    recurrence = service.recurrences.set(task, data)

    db.commit()

    return RecurrenceResponse.model_validate(recurrence)


@router.patch(
    "/{task_id}/recurrence",
    response_model=RecurrenceResponse,
)
def update_task_recurrence(
    task_id: int,
    data: RecurrenceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RecurrenceResponse:
    service = TaskService(db)

    task = service.get(task_id, current_user.id)
    recurrence = service.recurrences.update(task, data)

    db.commit()

    return RecurrenceResponse.model_validate(recurrence)


@router.delete(
    "/{task_id}/recurrence",
    response_model=MessageResponse,
)
def delete_task_recurrence(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    service = TaskService(db)

    task = service.get(task_id, current_user.id)
    service.recurrences.delete(task)

    db.commit()

    return MessageResponse(message="Task recurrence deleted")


@router.post(
    "/{task_id}/next-occurrence",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_next_occurrence(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskResponse:
    service = TaskService(db)

    task = service.get(task_id, current_user.id)
    next_task = RecurrenceService(db).create_next_instance(task)

    if next_task is None:
        raise AppException(
            status_code=400,
            detail="Task is not recurring or recurrence is finished",
            code="recurrence_not_available",
        )

    db.commit()

    return task_response(next_task)
