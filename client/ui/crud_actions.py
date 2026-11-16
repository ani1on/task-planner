"""Общие CRUD-действия страниц: диалоги, сохранение, удаление.

Миксины вызываются как слоты страниц (QWidget), поэтому все диалоги
и обращения к сервисам выполняются в GUI-потоке.
"""

from typing import Any

from client.api.models import Project, Task
from client.core.constants import (
    PROJECT_STATUS_ACTIVE,
    PROJECT_STATUS_ARCHIVED,
    STATUS_DONE,
    STATUS_TODO,
)
from client.core.worker import run_async
from client.ui.dialogs import ConfirmDialog, ProjectDialog, TaskDialog
from client.ui.error_handler import handle_api_error


class _ActionsMixin:
    task_service: Any = None
    project_service: Any = None

    def _dialog_failed(self, error: Exception):
        handle_api_error(error, self)

    def _after_change(self, _result):
        self.reload()


class TaskActionsMixin(_ActionsMixin):
    """Создание, редактирование, завершение и удаление задач."""

    def open_task_dialog(
        self,
        task: Task | None = None,
        project_id: int | None = None,
    ):
        if self.task_service is None or self.project_service is None:
            return

        self._dialog_task = task
        self._dialog_project_id = project_id

        run_async(
            self._load_dialog_context,
            self._show_task_dialog,
            self._dialog_failed,
        )

    def _load_dialog_context(self) -> dict:
        projects = self.project_service.list()
        members = self.project_service.members_map([project.id for project in projects])

        return {"projects": projects, "members": members}

    def _show_task_dialog(self, context: dict):
        dialog = TaskDialog(
            projects=context["projects"],
            members_map=context["members"],
            task=self._dialog_task,
            project_id=self._dialog_project_id,
            parent=self,
        )

        if dialog.exec() != TaskDialog.DialogCode.Accepted:
            return

        try:
            if self._dialog_task is None:
                self.task_service.create(**dialog.payload())
            else:
                self.task_service.update(self._dialog_task.id, **dialog.payload())
        except Exception as error:
            handle_api_error(error, self)
            return

        self.reload()

    def edit_task(self, task_id: int):
        task = getattr(self, "_task_models", {}).get(task_id)

        if task is None:
            self.reload()
            return

        self.open_task_dialog(task)

    def toggle_task(self, task_id: int, done: bool):
        if self.task_service is None:
            return

        status = STATUS_DONE if done else STATUS_TODO

        run_async(
            self.task_service.update,
            self._after_change,
            self._dialog_failed,
            task_id,
            status=status,
        )

    def delete_task(self, task_id: int):
        if self.task_service is None:
            return

        dialog = ConfirmDialog("Удалить задачу без возможности восстановления?", self)

        if dialog.exec() != ConfirmDialog.DialogCode.Accepted:
            return

        run_async(
            self.task_service.delete,
            self._after_change,
            self._dialog_failed,
            task_id,
        )


class ProjectActionsMixin(_ActionsMixin):
    """Создание, редактирование, архивация и удаление проектов."""

    def open_project_dialog(self, project: Project | None = None):
        if self.project_service is None:
            return

        dialog = ProjectDialog(project=project, parent=self)

        if dialog.exec() != ProjectDialog.DialogCode.Accepted:
            return

        try:
            if project is None:
                self.project_service.create(**dialog.payload())
            else:
                self.project_service.update(project.id, **dialog.payload())
        except Exception as error:
            handle_api_error(error, self)
            return

        self.reload()

    def edit_project(self, project_id: int):
        project = getattr(self, "_project_models", {}).get(project_id)

        if project is None:
            self.reload()
            return

        self.open_project_dialog(project)

    def archive_project(self, project_id: int):
        project = getattr(self, "_project_models", {}).get(project_id)

        if project is None or self.project_service is None:
            return

        status = (
            PROJECT_STATUS_ACTIVE
            if project.status == PROJECT_STATUS_ARCHIVED
            else PROJECT_STATUS_ARCHIVED
        )

        run_async(
            self.project_service.update,
            self._after_change,
            self._dialog_failed,
            project_id,
            status=status,
        )

    def delete_project(self, project_id: int):
        if self.project_service is None:
            return

        dialog = ConfirmDialog(
            "Удалить проект вместе со всеми задачами и заметками?",
            self,
        )

        if dialog.exec() != ConfirmDialog.DialogCode.Accepted:
            return

        run_async(
            self.project_service.delete,
            self._after_change,
            self._dialog_failed,
            project_id,
        )
