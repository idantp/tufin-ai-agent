"""
FastAPI application entry point.

Provides a multi-tool agent API with health checks, task submission,
and task retrieval endpoints. Uses async SQLite for persistence and
centralized configuration via pydantic-settings.
"""

import json
import logging
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from app.agent.graph import get_agent_graph, init_agent_graph
from app.config import get_settings
from app.database import (
    create_conversation,
    create_task,
    get_conversation,
    get_task,
    get_trace_steps,
    init_db,
    update_task,
)
from app.models import (
    HealthResponse,
    TaskRecord,
    TaskRequest,
    TaskResponse,
    TaskStatus,
    TraceStep,
    TraceStepType,
)


logger = logging.getLogger(__name__)

VERSION = "0.1.0"

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

    async with AsyncSqliteSaver.from_conn_string(settings.checkpoint_db_url) as checkpointer:
        init_agent_graph(checkpointer)
        logger.info("Agent graph compiled with checkpointer")

        yield

        logger.info("Shutting down")


app = FastAPI(
    title="Multi-Tool Agent API",
    description="A general-purpose AI agent with observability",
    version=VERSION,
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
    return HealthResponse(status="ok", version=VERSION)


@app.post("/task", response_model=TaskResponse)
async def create_task_endpoint(task_request: TaskRequest) -> TaskResponse:
    """
    Submit a new task to the agent.

    If ``conversation_id`` is provided the agent resumes the existing
    conversation (LangGraph reloads prior messages via the checkpointer).
    Otherwise a brand-new conversation is started.

    Args:
        task_request: Task request containing the input text and optional conversation_id.

    Returns:
        TaskResponse: Task ID, conversation ID, final answer, and execution trace.

    Raises:
        HTTPException: 500 if agent execution or persistence fails.
    """
    settings = get_settings()
    task_id = str(uuid.uuid4())
    start_time = time.perf_counter()

    # Resolve or create conversation
    conversation_id = task_request.conversation_id
    if conversation_id is not None:
        existing = await get_conversation(settings.database_url, conversation_id)
        if existing is None:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conversation_id = str(uuid.uuid4())
        await create_conversation(settings.database_url, conversation_id)

    logger.info(
        "Task received: %s | conversation: %s | input: %s",
        task_id, conversation_id, task_request.input[:50],
    )

    await create_task(settings.database_url, task_id, conversation_id, task_request.input)

    agent = get_agent_graph()
    config = {"configurable": {"thread_id": conversation_id}}

    try:
        result = await agent.ainvoke(
            {
                "messages": [HumanMessage(content=task_request.input)],
                "task_id": task_id,
                "agent_iteration": 0,
                "trace_step_index": 0,
                "tokens_usage": 0,
                "final_answer": "",
            },
            config=config,
        )

        final_answer: str = result.get("final_answer") or ""
        tokens_usage: int = result.get("tokens_usage", 0)
        latency_ms = int((time.perf_counter() - start_time) * 1000)

        await update_task(
            settings.database_url,
            task_id,
            final_answer=final_answer,
            status=TaskStatus.COMPLETED.value,
            token_usage=tokens_usage,
            latency_ms=latency_ms,
        )

        logger.info("Task completed: %s | latency: %sms | tokens: %s", task_id, latency_ms, tokens_usage)

        trace_steps_dicts = await get_trace_steps(settings.database_url, task_id)
        trace_steps = [
            TraceStep(
                step_index=s["step_index"],
                type=TraceStepType(s["type"]),
                description=s.get("description"),
                tool_name=s.get("tool_name"),
                tool_input=json.loads(s["tool_input"]) if s.get("tool_input") else None,
                tool_output=json.loads(s["tool_output"]) if s.get("tool_output") else None,
            )
            for s in trace_steps_dicts
        ]

        return TaskResponse(
            task_id=task_id,
            conversation_id=conversation_id,
            final_answer=final_answer,
            trace=trace_steps,
        )

    except Exception as e:
        latency_ms = int((time.perf_counter() - start_time) * 1000)
        logger.error("Task failed: %s | error: %s", task_id, str(e))
        await update_task(
            settings.database_url,
            task_id,
            final_answer=None,
            status=TaskStatus.FAILED.value,
            token_usage=0,
            latency_ms=latency_ms,
        )
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tasks/{task_id}", response_model=TaskRecord)
async def get_task_endpoint(task_id: str) -> TaskRecord:
    """
    Retrieve a task by ID.

    Args:
        task_id: The UUID of the task to retrieve.

    Returns:
        TaskRecord: Full task record with trace steps.

    Raises:
        HTTPException: 404 if task not found.
    """
    settings = get_settings()

    logger.info("Task retrieved: %s", task_id)

    # Get task from DB
    task_dict = await get_task(settings.database_url, task_id)
    if task_dict is None:
        raise HTTPException(status_code=404, detail="Task not found")

    # Get trace steps from DB
    trace_steps_dicts = await get_trace_steps(settings.database_url, task_id)

    # Reconstruct TraceStep models from DB dicts
    # TODO: implement this somewhere else.
    trace_steps = []
    for step_dict in trace_steps_dicts:
        tool_input = None
        if step_dict.get("tool_input"):
            tool_input = json.loads(step_dict["tool_input"])

        tool_output = None
        if step_dict.get("tool_output"):
            tool_output = json.loads(step_dict["tool_output"])

        trace_step = TraceStep(
            step_index=step_dict["step_index"],
            type=TraceStepType(step_dict["type"]),
            description=step_dict.get("description"),
            tool_name=step_dict.get("tool_name"),
            tool_input=tool_input,
            tool_output=tool_output,
        )
        trace_steps.append(trace_step)

    # Parse created_at timestamp
    created_at = datetime.fromisoformat(task_dict["created_at"])

    return TaskRecord(
        task_id=task_dict["task_id"],
        conversation_id=task_dict["conversation_id"],
        input=task_dict["input"],
        final_answer=task_dict.get("final_answer"),
        status=TaskStatus(task_dict["status"]),
        token_usage=task_dict.get("token_usage"),
        latency_ms=task_dict.get("latency_ms"),
        created_at=created_at,
        trace=trace_steps,
    )
