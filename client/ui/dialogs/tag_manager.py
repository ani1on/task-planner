from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from client.services.tags import TagService
from client.ui.components import PrimaryButton, SecondaryButton
from client.ui.dialogs.confirm import ConfirmDialog
from client.ui.error_handler import handle_api_error


class TagManagementPanel(QWidget):
    """Встроенное создание, переименование и удаление тегов проекта."""

    changed = Signal()

    def __init__(
        self,
        service: TagService,
        project_id: int,
        parent=None,
    ):
        super().__init__(parent)
        self.service = service
        self.project_id = project_id
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(8)

        self.items = QVBoxLayout()
        self.items.setSpacing(8)
        self.root_layout.addLayout(self.items)

        form = QHBoxLayout()
        self.new_name = QLineEdit()
        self.new_name.setPlaceholderText("Название нового тега")
        create = PrimaryButton("Создать")
        create.clicked.connect(self.create)
        form.addWidget(self.new_name, 1)
        form.addWidget(create)
        self.root_layout.addLayout(form)
        self.reload()

    def reload(self):
        while self.items.count():
            item = self.items.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        try:
            tags = self.service.list(self.project_id)
        except Exception as error:
            handle_api_error(error, self)
            return

        if not tags:
            self.items.addWidget(QLabel("Тегов пока нет"))
            return

        for tag in tags:
            row = QWidget()
            layout = QHBoxLayout(row)
            layout.setContentsMargins(0, 0, 0, 0)
            name = QLineEdit(tag.name)
            save = SecondaryButton("Сохранить")
            save.clicked.connect(
                lambda _=False, tag_id=tag.id, field=name: self.edit(
                    tag_id, field.text()
                )
            )
            delete = SecondaryButton("Удалить")
            delete.clicked.connect(
                lambda _=False, tag_id=tag.id: self.remove(tag_id)
            )
            layout.addWidget(name, 1)
            layout.addWidget(save)
            layout.addWidget(delete)
            self.items.addWidget(row)

    def create(self):
        name = self.new_name.text().strip()
        if not name:
            return
        try:
            self.service.create(self.project_id, name)
        except Exception as error:
            handle_api_error(error, self)
            return
        self.new_name.clear()
        self.reload()
        self.changed.emit()

    def edit(self, tag_id: int, name: str):
        name = name.strip()
        if not name:
            return
        try:
            self.service.update(tag_id, name=name)
        except Exception as error:
            handle_api_error(error, self)
            return
        self.reload()
        self.changed.emit()

    def remove(self, tag_id: int):
        if ConfirmDialog("Удалить тег проекта?", self).exec() != (
            ConfirmDialog.DialogCode.Accepted
        ):
            return
        try:
            self.service.delete(tag_id)
        except Exception as error:
            handle_api_error(error, self)
            return
        self.reload()
        self.changed.emit()
