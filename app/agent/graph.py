"""Graph for the agent."""
from langgraph.graph import StateGraph, START, END
from app.agent.state import AgentState
from langchain_core.messages import BaseMessage, AIMessage
from app.config import get_settings
from app.agent.reasoning_node import reasoning_node
from app.agent.tools_executer_node import tools_executer_node
from app.agent.max_iterations_answer_node import max_iterations_answer_node


def route_after_reasoning(state: AgentState) -> str:
    """Three-way router: tool execution, forced final answer, or end."""
    settings = get_settings()
    if state.get("agent_iteration", 0) > settings.agent_max_iterations:
        return "max_iterations_answer"
    last_message: BaseMessage = state["messages"][-1]
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools_execution"
    return "end"

def build_agent_graph() -> StateGraph:
    """Build the agent graph."""
    graph = StateGraph(AgentState)
    graph.add_node("reasoning", reasoning_node)
    graph.add_node("tools_execution", tools_executer_node)
    graph.add_node("max_iterations_answer", max_iterations_answer_node)

    graph.add_edge(START, "reasoning")
    graph.add_conditional_edges(
        "reasoning",
        route_after_reasoning,
        {
            "tools_execution": "tools_execution",
            "max_iterations_answer": "max_iterations_answer",
            "end": END,
        },
    )

    graph.add_edge("tools_execution", "reasoning")
    graph.add_edge("max_iterations_answer", END)
    return graph.compile()

multi_step_agent = build_agent_graph()
