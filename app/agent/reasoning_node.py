"""Reasoning node for the agent."""
from langchain_core.messages import BaseMessage
from langchain_core.messages import AIMessage
from app.agent.state import AgentState
from app.agent.llm import LLM_WITH_TOOLS
from app.models import TraceStepType
from app.database import insert_trace_step
from app.config import get_settings

async def reasoning_node(state: AgentState) -> AgentState:
    messages: list[BaseMessage] = state["messages"]
    task_id = state["task_id"]
    steps_count = state.get("steps_count", 0)
    response: AIMessage = await LLM_WITH_TOOLS.ainvoke(messages)
    settings = get_settings()
    content: str = ""
    if response.tool_calls:
        content = f"LLM decided to call {len(response.tool_calls)} tools: {[tool_call.get('name') for tool_call in response.tool_calls] }" 
    await insert_trace_step(
        settings.database_url,
        task_id,
        step_index=steps_count,
        type=TraceStepType.LLM_REASONING.value,
        content=content,
        tool_name=None,
        tool_input=None,
        tool_output=None,
    )
    tokens_used = (response.usage_metadata or {}).get("total_tokens", 0)

    return {
        "messages": [response],
        "steps_count": steps_count + 1,
        "tokens_usage": tokens_used,
    }
