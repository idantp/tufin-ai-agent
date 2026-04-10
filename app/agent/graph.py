"""Graph for the agent."""
from langgraph.graph import StateGraph, START, END
from app.agent.state import AgentState
from langchain_core.messages import BaseMessage, AIMessage
from app.config import get_settings
from app.agent.reasoning_node import reasoning_node
from app.agent.tools_executer_node import tools_executer_node


def should_call_tool(state: AgentState) -> bool:
    """Check if the agent should call a tool."""
    settings = get_settings()
    if state.get("agent_iteration", 0) >= settings.agent_max_iterations:
        return False
    last_message: BaseMessage = state["messages"][-1]
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return True
    return False

def build_agent_graph() -> StateGraph:
    """Build the agent graph."""
    graph = StateGraph(AgentState)
    graph.add_node("reasoning", reasoning_node)
    graph.add_node("tools_execution", tools_executer_node)

    graph.add_edge(START, "reasoning")
    graph.add_conditional_edges(
        "reasoning",
        should_call_tool,
        {
            True: "tools_execution",
            False: "reasoning",
        },
    )

    graph.add_edge("tools_execution", "reasoning")
    return graph.compile()

multi_step_agent = build_agent_graph()
