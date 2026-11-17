"""Общие CRUD-действия страниц: диалоги, сохранение, удаление.

Миксины вызываются как слоты страниц (QWidget), поэтому все диалоги
и обращения к сервисам выполняются в GUI-потоке.
"""

from datetime import datetime
from typing import Any

from client.core.constants import (
    STATUS_DONE,
    STATUS_TODO,
)
from client.core.worker import run_async
from client.services.comments import CommentService
from client.services.reminders import ReminderService
from client.services.tags import TagService
from client.ui.dialogs import (
    ConfirmDialog,
    ProjectDialog,
    TaskDialog,
)
from client.ui.dialogs.reminders import ReminderManagerPanel
from client.ui.dialogs.task_detail import CommentsSection, SubtasksSection, TagsSection
from client.ui.error_handler import handle_api_error


class _ActionsMixin:
    task_service: Any = None
    project_service: Any = None
    user_id: int | None = None

    def _dialog_failed(self, error: Exception):
        handle_api_error(error, self)

    def _after_change(self, _result):
        self.reload()


class TaskActionsMixin(_ActionsMixin):
    """Создание, редактирование, завершение и удаление задач."""

    def save_task_inline(self, task_id: int, fields: dict, card=None):
        if (
            card is not None
            and card.task.get("has_subtasks")
            and fields.get("status") == STATUS_DONE
            and card.task.get("status") != STATUS_DONE
        ):
            card.show_edit_error(
                "Нельзя завершить задачу, пока у неё есть подзадачи"
            )
            return

        if self.task_service is None:
            if card is not None:
                card.update_task(fields)
            for collection_name in ("all_tasks", "_all_tasks"):
                for task in getattr(self, collection_name, []):
                    if int(task.get("id") or 0) == task_id:
                        task.update(fields)
                        break
            return

        run_async(
            self.task_service.update,
            self._after_change,
            self._dialog_failed,
            task_id,
            **fields,
        )

    def open_task_dialog(
        self,
        project_id: int | None = None,
        due_at: datetime | None = None,
    ):
        if self.task_service is None or self.project_service is None:
            return

        self._dialog_project_id = project_id
        self._dialog_due_at = due_at

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
            project_id=self._dialog_project_id,
            due_at=self._dialog_due_at,
            require_due_date=self._dialog_due_at is not None,
            parent=self,
        )

        if dialog.exec() != TaskDialog.DialogCode.Accepted:
            return

        try:
            saved_task = self.task_service.create(**dialog.payload())
        except Exception as error:
            handle_api_error(error, self)
            return

        task_saved = getattr(self, "_task_dialog_saved", None)
        if self._dialog_due_at is not None and task_saved is not None:
            task_saved(saved_task)

        self.reload()

    def open_task_panel(self, task_id: int, panel_key: str):
        card = getattr(self, "_task_cards", {}).get(task_id)
        api = getattr(self, "api", None)
        if card is None or self.task_service is None or api is None:
            return
        if panel_key == "tags":
            panel = TagsSection(
                TagService(api),
                task_id,
                int(card.task.get("project_id") or 0),
                card,
            )
            panel.tags_changed.connect(
                lambda tags: card.update_tags(
                    [tag.name for tag in tags],
                    {tag.name: tag.color for tag in tags},
                )
            )
        elif panel_key == "subtasks":
            panel = SubtasksSection(self.task_service, task_id, card)
            if panel.has_subtasks is not None:
                card.set_has_subtasks(panel.has_subtasks)
            panel.subtasks_changed.connect(card.set_has_subtasks)
        elif panel_key == "comments":
            members = []
            project_id = int(card.task.get("project_id") or 0)
            if project_id and self.project_service is not None:
                try:
                    members = self.project_service.members(project_id)
                except Exception as error:
                    handle_api_error(error, self)
            panel = CommentsSection(
                CommentService(api), task_id, members, self.user_id, card
            )
        elif panel_key == "reminders":
            panel = ReminderManagerPanel(
                ReminderService(api), task_id=task_id, parent=card
            )
        else:
            return
        card.set_inline_panel(panel_key, panel)

    def toggle_task(self, task_id: int, done: bool):
        if self.task_service is None:
            return

        card = getattr(self, "_task_cards", {}).get(task_id)
        if done and card is not None and card.task.get("has_subtasks"):
            card.set_done(False)
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
    """Создание, архивация и удаление проектов."""

    def open_project_dialog(self):
        if self.project_service is None:
            return

        dialog = ProjectDialog(parent=self)

        if dialog.exec() != ProjectDialog.DialogCode.Accepted:
            return

        try:
            self.project_service.create(**dialog.payload())
        except Exception as error:
            handle_api_error(error, self)
            return

        self.reload()

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
