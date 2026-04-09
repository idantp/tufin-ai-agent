"""Tools executer node for the agent."""
from langchain_core.messages import AIMessage, ToolMessage
from app.agent.state import AgentState
from app.agent.llm import TOOLS_MAP
import json
from app.database import insert_trace_step
from app.config import get_settings
from app.models import TraceStepType

async def tools_executer_node(state: AgentState) -> AgentState:
    """Execute the tools."""
    last_message: AIMessage = state["messages"][-1]
    settings = get_settings()
    task_id = state["task_id"]
    step_index = state.get("steps_count", 0)


    tools_results = []
    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        tool_call_id = tool_call["id"]
        tool_func = TOOLS_MAP.get(tool_name)
        if tool_func is None:
            result = json.dumps({"error": f"Tool {tool_name} not found"})
        else:
            await insert_trace_step(
                settings.database_url,
                task_id,
                step_index=step_index,
                type=TraceStepType.TOOL_CALL.value,
                content=f"Calling tool {tool_name}",
                tool_name=tool_name,
                tool_input=json.dumps(tool_args),
                tool_output=None,
            )
            step_index += 1
            try:    
                result = await tool_func.ainvoke(tool_args)

                await insert_trace_step(
                    settings.database_url,
                    task_id,
                    step_index=step_index,
                    type=TraceStepType.TOOL_RESULT.value,
                    content=f"Called tool {tool_name} with args {tool_args} successfully",
                    tool_name=tool_name,
                    tool_input=json.dumps(tool_args),
                    tool_output=result,
                )
                step_index += 1
            except Exception as e:
                result = json.dumps({"error": str(e)})
        # TODO: log the result
        tools_results.append(ToolMessage(content=result, tool_call_id=tool_call_id))

    return {
        "messages": tools_results,
        "steps_count": step_index
    }