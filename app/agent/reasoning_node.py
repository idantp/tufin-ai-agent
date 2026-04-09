"""Reasoning node for the agent."""
from langchain_core.messages import BaseMessage
from langchain_core.messages import AIMessage
from app.agent.state import AgentState
from app.agent.llm import LLM_WITH_TOOLS

def reasoning_node(state: AgentState) -> AgentState:
    messages: list[BaseMessage] = state["messages"]

    response: AIMessage = LLM_WITH_TOOLS.invoke(messages)
    # TODO: log the response
    if response.tool_calls:
        for tool_call in response.tool_calls:
            # logs and db insertions if needed
            pass
    return {
        "messages": [response],
        "steps_count": state.get("steps_count", 0) + 1
    }
