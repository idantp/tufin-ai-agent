"""Reasoning node for the agent."""

import logging

from langchain_core.messages import AIMessage, BaseMessage, SystemMessage

from app.agent.llm import LLM_WITH_TOOLS
from app.agent.prompts import MAX_ITERATIONS_WARNING, SYSTEM_PROMPT
from app.agent.state import AgentState
from app.config import get_settings
from app.database import insert_trace_step
from app.models import TraceStepType


logger = logging.getLogger(__name__)


def _prepare_messages(
    messages: list[BaseMessage], near_limit: bool
) -> list[BaseMessage]:
    """Return a copy of the conversation with system prompt and iteration warning injected."""
    prepared = list(messages)
    if not prepared or not isinstance(prepared[0], SystemMessage):
        prepared.insert(0, SystemMessage(content=SYSTEM_PROMPT))
    if near_limit:
        prepared.append(SystemMessage(content=MAX_ITERATIONS_WARNING))
    return prepared


def _build_step_description(response: AIMessage, near_limit: bool) -> str:
    """Derive a human-readable trace description and log the LLM decision."""
    if response.tool_calls and not near_limit:
        tool_names = [tc.get("name") for tc in response.tool_calls]
        description = f"Model decided to call tools: {', '.join(tool_names)}"
        logger.info("LLM decided to call %d tool(s): %s", len(response.tool_calls), tool_names)
    elif response.tool_calls and near_limit:
        tool_names = [tc.get("name") for tc in response.tool_calls]
        description = f"Generating final answer — iteration limit reached (ignoring tool calls: {', '.join(tool_names)})"
        logger.info("Iteration limit reached; ignoring %d tool call(s): %s", len(response.tool_calls), tool_names)
    else:
        description = "Generating final answer — sufficient information gathered"
        logger.info("LLM produced final text response (%d chars)", len(response.content or ""))
    return description


async def _record_trace(
    task_id: str, trace_step_index: int, description: str, db_url: str
) -> None:
    """Persist a reasoning trace step."""
    await insert_trace_step(
        db_url,
        task_id,
        step_index=trace_step_index,
        type=TraceStepType.LLM_REASONING.value,
        tool_name=None,
        tool_input=None,
        tool_output=None,
        description=description,
    )


def _build_return_state(
    response: AIMessage, state: AgentState, agent_iteration: int, trace_step_index: int
) -> AgentState:
    """Assemble the state update returned by the reasoning node."""
    tokens_used = (response.usage_metadata or {}).get("total_tokens", 0)
    final_answer = (
        state.get("final_answer", "")
        if response.tool_calls
        else response.content or ""
    )
    return {
        "messages": [response],
        "trace_step_index": trace_step_index + 1,
        "tokens_usage": tokens_used,
        "agent_iteration": agent_iteration + 1,
        "final_answer": final_answer,
    }


async def reasoning_node(state: AgentState) -> AgentState:
    settings = get_settings()
    task_id = state["task_id"]
    agent_iteration = state.get("agent_iteration", 0)
    trace_step_index = state.get("trace_step_index", 0)
    near_limit = agent_iteration > settings.agent_max_iterations

    messages = _prepare_messages(state["messages"], near_limit)
    logger.info("LLM call #%d for task %s (%d messages in context)", agent_iteration, task_id, len(messages))

    response: AIMessage = await LLM_WITH_TOOLS.ainvoke(messages)

    description = _build_step_description(response, near_limit)
    await _record_trace(task_id, trace_step_index, description, settings.database_url)

    return _build_return_state(response, state, agent_iteration, trace_step_index)
