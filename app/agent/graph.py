"""Graph for the agent."""
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import StateGraph, START, END
from app.agent.state import AgentState
from langchain_core.messages import BaseMessage, AIMessage
from app.config import get_settings
from app.agent.reasoning_node import reasoning_node
from app.agent.tools_executer_node import tools_executer_node
from app.agent.max_iterations_answer_node import max_iterations_answer_node


_compiled_graph = None


def should_call_tools_router(state: AgentState) -> str:
    """Binary router: does the LLM want to call tools or is this a final answer?"""
    last_message: BaseMessage = state["messages"][-1]
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools_execution"
    return "end"


def max_iterations_router(state: AgentState) -> str:
    """Binary router: has the agent exhausted its iteration budget?"""
    settings = get_settings()
    if state.get("agent_iteration", 0) >= settings.agent_max_iterations:
        return "max_iterations_answer"
    return "reasoning"


def build_agent_graph(checkpointer: BaseCheckpointSaver | None = None) -> StateGraph:
    """Build and compile the agent graph with an optional checkpointer."""
    graph = StateGraph(AgentState)
    graph.add_node("reasoning", reasoning_node)
    graph.add_node("tools_execution", tools_executer_node)
    graph.add_node("max_iterations_answer", max_iterations_answer_node)

    graph.add_edge(START, "reasoning")
    graph.add_conditional_edges(
        "reasoning",
        should_call_tools_router,
        {
            "tools_execution": "tools_execution",
            "end": END,
        },
    )
    graph.add_conditional_edges(
        "tools_execution",
        max_iterations_router,
        {
            "reasoning": "reasoning",
            "max_iterations_answer": "max_iterations_answer",
        },
    )
    graph.add_edge("max_iterations_answer", END)
    return graph.compile(checkpointer=checkpointer)


def init_agent_graph(checkpointer: BaseCheckpointSaver) -> None:
    """Compile the graph with the given checkpointer and store it as a singleton."""
    global _compiled_graph
    _compiled_graph = build_agent_graph(checkpointer)


def get_agent_graph():
    """Return the compiled agent graph singleton."""
    if _compiled_graph is None:
        raise RuntimeError("Agent graph not initialized — call init_agent_graph() first")
    return _compiled_graph
