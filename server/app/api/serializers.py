from ..models.project import Project
from ..models.task import Task
from ..schemas.project import ProjectResponse
from ..schemas.tag import TagResponse
from ..schemas.task import TaskResponse


def task_response(task: Task) -> TaskResponse:
    data = TaskResponse.model_validate(task)

    tags = [
        TagResponse.model_validate(link.tag)
        for link in task.task_tags
    ]

    return data.model_copy(update={"tags": tags})


def project_response(
    project: Project,
    *,
    role: str | None = None,
    progress: tuple[int, int] | None = None,
) -> ProjectResponse:
    data = ProjectResponse.model_validate(project)
    update: dict = {}

    if role is not None:
        update["role"] = role

    if progress is not None:
        total, done = progress
        update["tasks_total"] = total
        update["tasks_done"] = done
        update["progress"] = int(done / total * 100) if total else 0

    return data.model_copy(update=update)
