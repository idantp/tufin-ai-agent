"""State for the agent."""

import operator
from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """State for the agent."""
    messages: Annotated[list[BaseMessage], add_messages]
    agent_iteration: int
    trace_step_index: int
    task_id: str
    tokens_usage: Annotated[int, operator.add]
    final_answer: str
