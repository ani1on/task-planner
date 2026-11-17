from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from client.api.models import Project
from client.services.projects import ProjectService
from client.ui.components import PrimaryButton, SecondaryButton, TextInput
from client.ui.dialogs.confirm import ConfirmDialog
from client.ui.error_handler import handle_api_error

ROLES = (
    ("Администратор", "admin"),
    ("Участник", "member"),
    ("Наблюдатель", "viewer"),
)


class ProjectMembersPanel(QWidget):
    """Inline-панель участников проекта."""

    def __init__(
        self,
        project: Project,
        service: ProjectService,
        parent=None,
    ):
        super().__init__(parent)
        self.project = project
        self.service = service

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)
        self.members_layout = QVBoxLayout()
        self.members_layout.setSpacing(8)
        root.addLayout(self.members_layout)

        invite = QHBoxLayout()
        self.email = TextInput("email@example.com")
        self.role = self._role_combo()
        button = PrimaryButton("Пригласить")
        button.clicked.connect(self.add_member)
        invite.addWidget(self.email, 1)
        invite.addWidget(self.role)
        invite.addWidget(button)
        root.addLayout(invite)
        self.reload()

    @staticmethod
    def _role_combo(selected: str = "member") -> QComboBox:
        combo = QComboBox()
        if selected == "owner":
            combo.addItem("Владелец", "owner")
        for label, value in ROLES:
            combo.addItem(label, value)
        index = combo.findData(selected)
        combo.setCurrentIndex(max(index, 0))
        return combo

    def reload(self):
        while self.members_layout.count():
            item = self.members_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        try:
            members = self.service.members(self.project.id)
        except Exception as error:
            handle_api_error(error, self)
            return

        if not members:
            self.members_layout.addWidget(QLabel("Участников нет"))
            return

        for member in members:
            row = QFrame()
            row.setProperty("component", "card")
            layout = QHBoxLayout(row)
            name = QLabel(member.nick_name or member.email or f"#{member.user_id}")
            role = self._role_combo(member.role)
            role.setEnabled(member.role != "owner")
            role.currentIndexChanged.connect(
                lambda _index, member=member, combo=role: self.update_role(
                    member.user_id,
                    combo.currentData(),
                )
            )
            remove = SecondaryButton("Удалить")
            remove.setEnabled(member.role != "owner")
            remove.clicked.connect(
                lambda _=False, user_id=member.user_id: self.remove_member(user_id)
            )
            layout.addWidget(name, 1)
            layout.addWidget(role)
            layout.addWidget(remove)
            self.members_layout.addWidget(row)

    def add_member(self):
        email = self.email.text().strip()
        if not email:
            return
        try:
            self.service.add_member(
                self.project.id,
                email=email,
                role=self.role.currentData(),
            )
        except Exception as error:
            handle_api_error(error, self)
            return
        self.email.clear()
        self.reload()

    def update_role(self, user_id: int, role: str):
        try:
            self.service.update_member_role(self.project.id, user_id, role)
        except Exception as error:
            handle_api_error(error, self)
        self.reload()

    def remove_member(self, user_id: int):
        if ConfirmDialog("Удалить участника из проекта?", self).exec() != (
            ConfirmDialog.DialogCode.Accepted
        ):
            return
        try:
            self.service.remove_member(self.project.id, user_id)
        except Exception as error:
            handle_api_error(error, self)
            return
        self.reload()
