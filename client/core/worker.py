from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QObject, QRunnable, Qt, QThreadPool, Signal, Slot
from PySide6.QtWidgets import QLabel


class ApiWorker(QRunnable):
    """Выполняет блокирующий вызов API в фоновом потоке.

    Результат и ошибка передаются через сигналы в потоке GUI.
    """

    class Signals(QObject):
        success = Signal(object)
        error = Signal(object)

    def __init__(self, fn: Callable[..., Any], *args: Any, **kwargs: Any):
        super().__init__()

        self.fn = fn
        self.args = args
        self.kwargs = kwargs

        self.signals = ApiWorker.Signals()

    @Slot()
    def run(self) -> None:
        try:
            result = self.fn(*self.args, **self.kwargs)
        except Exception as error:
            self.signals.error.emit(error)
        else:
            self.signals.success.emit(result)


def run_async(
    fn: Callable[..., Any],
    on_success: Callable[[Any], None],
    on_error: Callable[[Exception], None] | None = None,
    *args: Any,
    **kwargs: Any,
) -> ApiWorker:
    """Запускает ``fn`` в пуле потоков и связывает колбэки."""
    worker = ApiWorker(fn, *args, **kwargs)

    worker.signals.success.connect(on_success)

    if on_error is not None:
        worker.signals.error.connect(on_error)

    QThreadPool.globalInstance().start(worker)

    return worker


class LoadingWidget(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setText("Загрузка...")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.hide()

    def start(self):
        self.show()

    def stop(self):
        self.hide()


