"""Node that generates a final answer when the agent exceeds its iteration limit."""

import logging

from langchain_core.messages import AIMessage, BaseMessage, SystemMessage

from app.agent.llm import LLM
from app.agent.prompts import MAX_ITERATIONS_SYSTEM_PROMPT, MAX_ITERATIONS_WARNING
from app.agent.state import AgentState
from app.config import get_settings
from app.database import insert_trace_step
from app.models import TraceStepType

logger = logging.getLogger(__name__)


def _prepare_messages(messages: list[BaseMessage]) -> list[BaseMessage]:
    """Return conversation with system prompt and iteration-limit warning injected."""
    prepared = list(messages)
    if not prepared or not isinstance(prepared[0], SystemMessage):
        prepared.insert(0, SystemMessage(content=MAX_ITERATIONS_SYSTEM_PROMPT))
    prepared.append(SystemMessage(content=MAX_ITERATIONS_WARNING))
    return prepared


async def max_iterations_answer_node(state: AgentState) -> AgentState:
    """Invoke the LLM without tools to force a text-only final answer."""
    settings = get_settings()
    task_id = state["task_id"]
    trace_step_index = state.get("trace_step_index", 0)

    messages = _prepare_messages(state["messages"])
    logger.info(
        "Max iterations reached for task %s — generating forced final answer (%d messages in context)",
        task_id,
        len(messages),
    )

    response: AIMessage = await LLM.ainvoke(messages)

    tokens_used = (response.usage_metadata or {}).get("total_tokens", 0)
    description = "Generating final answer — iteration limit reached"
    logger.info("Forced final answer produced (%d chars)", len(response.content or ""))

    await insert_trace_step(
        settings.database_url,
        task_id,
        step_index=trace_step_index,
        type=TraceStepType.FINAL_ANSWER.value,
        tool_name=None,
        tool_input=None,
        tool_output=None,
        description=description,
    )

    return {
        "messages": [response],
        "trace_step_index": trace_step_index + 1,
        "tokens_usage": tokens_used,
        "final_answer": response.content or "",
    }
