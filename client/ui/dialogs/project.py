from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QPlainTextEdit,
)

from client.api.models import Project
from client.core.constants import (
    PROJECT_COLOR_LABELS,
    PROJECT_STATUS_LABELS,
)
from client.ui.components import (
    FormField,
    PrimaryButton,
    SecondaryButton,
    TextInput,
)

from .base import BaseDialog


class ProjectDialog(BaseDialog):
    """Создание и редактирование проекта."""

    def __init__(
        self,
        project: Project | None = None,
        parent=None,
    ):
        super().__init__(parent)

        self.project = project

        self.setWindowTitle(
            "Новый проект" if project is None else "Редактирование проекта"
        )
        self.setMinimumWidth(480)

        self.layout.setContentsMargins(24, 22, 24, 20)
        self.layout.setSpacing(14)

        self.name_field = FormField(
            "Название",
            TextInput("Например: Дипломный проект"),
        )

        self.color_combo = QComboBox()
        for color, label in PROJECT_COLOR_LABELS.items():
            self.color_combo.addItem(label, color)

        self.color_field = FormField("Цвет", self.color_combo)

        self.description_edit = QPlainTextEdit()
        self.description_edit.setPlaceholderText("Цель проекта и договорённости")
        self.description_edit.setFixedHeight(96)

        self.description_field = FormField("Описание", self.description_edit)

        self.layout.addWidget(self.name_field)
        self.layout.addWidget(self.color_field)
        self.layout.addWidget(self.description_field)

        self.status_combo = None

        if project is not None:
            self.status_combo = QComboBox()
            for status, label in PROJECT_STATUS_LABELS.items():
                self.status_combo.addItem(label, status)

            self.layout.addWidget(FormField("Статус", self.status_combo))

        buttons = QHBoxLayout()
        buttons.setSpacing(8)

        cancel = SecondaryButton("Отмена")
        cancel.clicked.connect(self.reject)

        save = PrimaryButton("Создать" if project is None else "Сохранить")
        save.setDefault(True)
        save.clicked.connect(self.accept)

        buttons.addStretch()
        buttons.addWidget(cancel)
        buttons.addWidget(save)

        self.layout.addLayout(buttons)

        self._fill()

        self.name_field.field.setFocus()

    def _fill(self):
        if self.project is None:
            return

        self.name_field.field.setText(self.project.name)
        self.description_edit.setPlainText(self.project.description or "")

        color_index = self.color_combo.findData(self.project.color)
        if color_index >= 0:
            self.color_combo.setCurrentIndex(color_index)

        if self.status_combo is not None:
            status_index = self.status_combo.findData(self.project.status)
            if status_index >= 0:
                self.status_combo.setCurrentIndex(status_index)

    def accept(self):
        if not self.name_field.value().strip():
            self.name_field.set_error("Введите название проекта")
            return

        super().accept()

    def payload(self) -> dict:
        data = {
            "name": self.name_field.value().strip(),
            "description": self.description_edit.toPlainText().strip() or None,
            "color": self.color_combo.currentData(),
        }

        if self.status_combo is not None:
            data["status"] = self.status_combo.currentData()

        return data
