"""
Pydantic models for the multi-tool agent API.

This module defines all data schemas used across the application:
- Request/response models for API endpoints
- Internal models for agent execution traces
- Database record models for persistence

No business logic lives here - these are pure data shapes.
"""


from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class TraceStepType(str, Enum):
    """Valid types for a trace step in the agent's execution."""

    LLM_REASONING = "llm_reasoning"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    FINAL_ANSWER = "final_answer"


class TaskStatus(str, Enum):
    """Valid statuses for a task."""

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class TraceStep(BaseModel):
    """
    Represents one step in the agent's reasoning and execution trace.

    Each step captures either LLM reasoning, a tool invocation, a tool result,
    or the final answer. Steps are ordered by step_index.
    """

    step_index: int
    type: TraceStepType
    content: str | None = None
    tool_name: str | None = None
    tool_input: dict | None = None
    tool_output: dict | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))

    model_config = ConfigDict(use_enum_values=True)


class TaskRequest(BaseModel):
    """
    Request body for POST /task endpoint.

    Contains the natural language task the user wants the agent to solve.
    """

    input: str = Field(
        min_length=1,
        max_length=2000,
        description="The natural language task for the agent to solve",
    )


class TaskResponse(BaseModel):
    """
    Response returned immediately after POST /task completes.

    Contains the agent's final answer, execution trace, and performance metrics.
    """

    task_id: str
    final_answer: str
    trace: list[TraceStep]
    token_usage: int
    latency_ms: int

    model_config = ConfigDict(use_enum_values=True)


class TaskRecord(BaseModel):
    """
    Full task record retrieved from the database.

    Represents a complete stored task including its input, output, status,
    metrics, and full execution trace.
    """

    task_id: str
    input: str
    final_answer: str | None = None
    status: TaskStatus
    token_usage: int | None = None
    latency_ms: int | None = None
    created_at: datetime
    trace: list[TraceStep] = []

    model_config = ConfigDict(use_enum_values=True)


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    version: str
