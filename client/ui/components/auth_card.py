from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QVBoxLayout,
)


class AuthCard(QFrame):
    """Центрированная карточка для экранов входа и регистрации."""

    def __init__(
        self,
        title: str,
        subtitle: str = "",
        parent=None,
    ):
        super().__init__(parent)

        self.setObjectName("AuthCard")
        self.setMaximumWidth(440)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(6)

        logo = QLabel("TP")
        logo.setObjectName("AuthLogo")
        logo.setFixedSize(48, 48)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_label = QLabel(title)
        title_label.setObjectName("AuthTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("AuthSubtitle")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setWordWrap(True)

        layout.addWidget(logo, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addSpacing(12)
        layout.addWidget(title_label)

        if subtitle:
            layout.addWidget(subtitle_label)

        layout.addSpacing(18)

        self.body = QVBoxLayout()
        self.body.setSpacing(14)

        layout.addLayout(self.body)

        self.footer = QVBoxLayout()
        self.footer.setSpacing(8)

        layout.addSpacing(6)
        layout.addLayout(self.footer)
