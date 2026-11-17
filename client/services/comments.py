from client.api.client import ApiClient
from client.api.mapper import comment_from_dict
from client.api.models import Comment


class CommentService:
    """Комментарии к задачам."""

    def __init__(self, api: ApiClient):
        self.api = api

    def list(self, task_id: int) -> list[Comment]:
        response = self.api.get("/comments", params={"task_id": task_id}) or []

        return [comment_from_dict(item) for item in response]

    def get(self, comment_id: int) -> Comment:
        response = self.api.get(f"/comments/{comment_id}")

        return comment_from_dict(response)

    def create(self, task_id: int, content: str) -> Comment:
        response = self.api.post(
            "/comments",
            json={"task_id": task_id, "content": content},
        )

        return comment_from_dict(response)

    def update(self, comment_id: int, content: str) -> Comment:
        response = self.api.patch(
            f"/comments/{comment_id}",
            json={"content": content},
        )

        return comment_from_dict(response)

    def delete(self, comment_id: int) -> None:
        self.api.delete(f"/comments/{comment_id}")
