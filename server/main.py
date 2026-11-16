import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .app.api.router import api_router
from .app.config import settings
from .app.core.errors import AppException
from .app.core.logging import setup_logging
from .app.realtime import set_event_loop
from .app.services.reminder_worker import reminder_worker_loop

setup_logging(settings.log_level)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    set_event_loop(asyncio.get_running_loop())

    worker: asyncio.Task[None] | None = None

    if settings.reminders_worker_enabled:
        worker = asyncio.create_task(reminder_worker_loop())
        logger.info("Reminder worker started")

    try:
        yield
    finally:
        if worker is not None:
            worker.cancel()

            try:
                await worker
            except asyncio.CancelledError:
                pass

            logger.info("Reminder worker stopped")

        set_event_loop(None)


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    debug=settings.app_debug,
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

cors_origins = [
    origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------


@app.exception_handler(AppException)
async def app_exception_handler(
    request: Request,
    exc: AppException,
) -> JSONResponse:
    logger.warning(
        "Application error: %s %s - %s",
        request.method,
        request.url.path,
        exc.detail,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.code,
            "detail": exc.detail,
            "extra": exc.extra,
        },
    )


@app.exception_handler(Exception)
async def unexpected_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    logger.exception(
        "Unhandled exception: %s %s",
        request.method,
        request.url.path,
    )

    return JSONResponse(
        status_code=500,
        content={
            "code": "internal_server_error",
            "detail": "Internal server error",
            "extra": {},
        },
    )


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------


app.include_router(api_router)
