from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from ...database import get_db
from ...schemas.common import (
    DatabaseHealthResponse,
    HealthResponse,
)

router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


@router.get(
    "",
    response_model=HealthResponse,
)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get(
    "/db",
    response_model=DatabaseHealthResponse,
)
def health_db(
    db: Session = Depends(get_db),
) -> DatabaseHealthResponse:
    db.execute(text("SELECT 1"))

    return DatabaseHealthResponse(
        status="ok",
        database="connected",
    )
