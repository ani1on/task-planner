from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLayout,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from client.ui.components import SecondaryButton, SectionTitle


def clear_layout(layout: QLayout):
    """Рекурсивно удаляет виджеты и вложенные layout'ы."""
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()

        if widget is not None:
            widget.deleteLater()
            continue

        child = item.layout()

        if child is not None:
            clear_layout(child)


class BasePage(QWidget):
    """Базовый экран: заголовок с действиями и прокручиваемое тело."""

    def __init__(
        self,
        title: str,
        subtitle: str = "",
        parent=None,
    ):
        super().__init__(parent)

        self.setObjectName("Page")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        header = QWidget()
        header.setObjectName("PageHeader")

        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(28, 22, 28, 10)
        header_layout.setSpacing(12)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)

        title_label = QLabel(title)
        title_label.setObjectName("PageTitle")

        title_layout.addWidget(title_label)

        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setObjectName("PageSubtitle")
            title_layout.addWidget(subtitle_label)

        self.actions_layout = QHBoxLayout()
        self.actions_layout.setSpacing(8)

        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        header_layout.addLayout(self.actions_layout)

        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("PageScroll")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        body = QWidget()
        body.setObjectName("PageBody")

        self.content_layout = QVBoxLayout(body)
        self.content_layout.setContentsMargins(28, 8, 28, 28)
        self.content_layout.setSpacing(16)

        self.scroll_area.setWidget(body)

        root.addWidget(header)
        root.addWidget(self.scroll_area, 1)

    def add_action(self, widget):
        self.actions_layout.addWidget(widget)

    def add_section(self, title: str):
        self.content_layout.addWidget(SectionTitle(title))

    # ------------------------------------------------------------------
    # Состояния загрузки данных
    # ------------------------------------------------------------------

    def reload(self):
        """Перезагружает данные страницы. Переопределяется наследниками."""

    def clear_content(self):
        clear_layout(self.content_layout)

    def scroll_to_widget(self, widget: QWidget):
        self.scroll_area.ensureWidgetVisible(widget, 0, 24)
        widget.setProperty("searchTarget", True)
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()

        timer = QTimer(widget)
        timer.setSingleShot(True)
        timer.timeout.connect(lambda: self._clear_search_target(widget))
        timer.start(1800)

    @staticmethod
    def _clear_search_target(widget: QWidget):
        widget.setProperty("searchTarget", False)
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()

    def show_loading(self, message: str = "Загрузка..."):
        self.clear_content()

        label = QLabel(message)
        label.setProperty("role", "muted")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.content_layout.addWidget(label)

    def show_error(self, message: str, on_retry=None):
        self.clear_content()

        container = QWidget()

        layout = QVBoxLayout(container)
        layout.setSpacing(12)

        label = QLabel(message)
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(label)

        if on_retry is not None:
            button = SecondaryButton("Повторить")
            button.clicked.connect(on_retry)
            layout.addWidget(button, 0, Qt.AlignmentFlag.AlignHCenter)

        self.content_layout.addWidget(container)
