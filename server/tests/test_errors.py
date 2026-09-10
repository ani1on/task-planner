from fastapi import FastAPI
from fastapi.testclient import TestClient

from server.app.core.errors import AppException


def test_app_exception_handler() -> None:
    test_app = FastAPI()

    @test_app.exception_handler(AppException)
    async def handler(_, exc: AppException):
        from fastapi.responses import JSONResponse

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": exc.code,
                "detail": exc.detail,
                "extra": exc.extra,
            },
        )

    @test_app.get("/test")
    def test_endpoint():
        raise AppException(
            status_code=404,
            detail="Not found",
            code="not_found",
        )

    client = TestClient(test_app)

    response = client.get("/test")

    assert response.status_code == 404
    assert response.json()["code"] == "not_found"
