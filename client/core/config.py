import os


class Config:
    API_URL = os.getenv(
        "TASK_PLANNER_API_URL",
        "http://localhost:8000",
    )

    API_TIMEOUT = int(
        os.getenv(
            "TASK_PLANNER_API_TIMEOUT",
            "10",
        )
    )
