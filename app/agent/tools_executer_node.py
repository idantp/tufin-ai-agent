"""Tools executer node for the agent."""
from langchain_core.messages import AIMessage, ToolMessage
from app.agent.state import AgentState
from app.agent.llm import TOOLS_MAP
import json

def tools_executer_node(state: AgentState) -> AgentState:
    """Execute the tools."""
    last_message: AIMessage = state["messages"][-1]
    
    tools_results = []
    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        tool_call_id = tool_call["id"]
        tool_func = TOOLS_MAP.get(tool_name)
        if tool_func is None:
            result = json.dumps({"error": f"Tool {tool_name} not found"})
        else:
            try:    
                result = tool_func.invoke(tool_args)
            except Exception as e:
                result = json.dumps({"error": str(e)})
        # TODO: log the result
        tools_results.append(ToolMessage(content=result, tool_call_id=tool_call_id))

    return {
        "messages": [tools_results],
        "steps_count": state.get("steps_count", 0) + len(tools_results)
    }