from fastapi import FastAPI
from sqlalchemy import text

from .app.database import engine

app = FastAPI(
    title="Task Planner API",
    version="0.1.0",
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/health/db")
def health_db():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    return {
        "status": "ok",
        "database": "connected",
    }
