from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot


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


# QThreadPool не держит Python-ссылок на QRunnable: без этого набора
# объект мог быть собран сборщиком мусора прямо во время запроса,
# а вместе с ним исчезал и объект signals.
_ACTIVE_WORKERS: set[ApiWorker] = set()


def run_async(
    fn: Callable[..., Any],
    on_success: Callable[[Any], None],
    on_error: Callable[[Exception], None] | None = None,
    *args: Any,
    **kwargs: Any,
) -> ApiWorker:
    """Запускает ``fn`` в пуле потоков и связывает колбэки."""
    worker = ApiWorker(fn, *args, **kwargs)

    def _release(*_: Any) -> None:
        _ACTIVE_WORKERS.discard(worker)

    worker.signals.success.connect(on_success)

    if on_error is not None:
        worker.signals.error.connect(on_error)

    worker.signals.success.connect(_release)
    worker.signals.error.connect(_release)

    _ACTIVE_WORKERS.add(worker)

    QThreadPool.globalInstance().start(worker)

    return worker
