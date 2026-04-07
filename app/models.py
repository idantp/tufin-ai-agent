"""Models for the Application."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    version: str


class TaskRequest(BaseModel):
    """Request model for task submission."""

    input: str


class TaskResponse(BaseModel):
    """Response model for task submission and retrieval."""

    task_id: str
    final_answer: str
    trace: list
