from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtWebSockets import QWebSocket


class RealtimeClient(QObject):
    event_received = Signal(dict)

    def __init__(self, api_base_url: str, token: str | None = None, parent=None):
        super().__init__(parent)
        self.socket = QWebSocket()
        self.base_url = api_base_url.rstrip("/")
        self.token = token

        self.socket.textMessageReceived.connect(self._on_message)
        self.socket.connected.connect(self._on_connected)

    def connect(self):
        url = self.base_url.replace("http", "ws") + "/ws"
        if self.token:
            url += f"?token={self.token}"
        self.socket.open(QUrl(url))

    def _on_connected(self):
        self.socket.sendTextMessage('{"action": "ping"}')

    def _on_message(self, message: str):
        import json

        try:
            data = json.loads(message)
        except Exception:
            return
        self.event_received.emit(data)

    def join_project(self, project_id: int):
        self.socket.sendTextMessage(
            f'{{"action": "join_project", "project_id": {project_id}}}'
        )

    def close(self):
        self.socket.close()
