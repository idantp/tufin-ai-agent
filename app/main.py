"""
FastAPI application entry point.

Provides a multi-tool agent API with health checks, task submission,
and task retrieval endpoints. Uses async SQLite for persistence and
centralized configuration via pydantic-settings.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

from app.config import get_settings
from app.database import init_db
from app.models import HealthResponse, TaskRequest, TaskResponse


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup (database initialization, logging configuration) and
    shutdown (cleanup logging) events.
    """
    settings = get_settings()

    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    await init_db(settings.database_url)
    logger.info("Database initialized")

    yield

    logger.info("Shutting down")


app = FastAPI(
    title="Multi-Tool Agent API",
    description="A general-purpose AI agent with observability",
    version="0.1.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming HTTP requests at INFO level."""
    logger.info("%s %s", request.method, request.url.path)
    response = await call_next(request)
    return response


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """
    Health check endpoint.

    Returns:
        HealthResponse: Status and version information.
    """
    return HealthResponse(status="ok", version="0.1.0")


@app.post("/task", response_model=TaskResponse)
async def create_task(task_request: TaskRequest) -> TaskResponse:
    """
    Submit a new task to the agent (stub implementation).

    Args:
        task_request: Task request containing the input text.

    Returns:
        TaskResponse: Task ID, final answer, and execution trace.
    """
    return TaskResponse(
        task_id="stub",
        final_answer="not implemented",
        trace=[],
    )


@app.get("/tasks/{task_id}")
async def get_task_by_id(task_id: str):
    """
    Retrieve a task by ID (stub implementation).

    Args:
        task_id: The UUID of the task to retrieve.

    Returns:
        HTTP 501 Not Implemented.
    """
    from fastapi import Response

    return Response(status_code=501, content="Not Implemented")
