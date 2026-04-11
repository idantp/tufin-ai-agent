"""Tools executer node for the agent."""

import json
import logging

from langchain_core.messages import AIMessage, ToolMessage

from app.agent.llm import TOOLS_MAP
from app.agent.state import AgentState
from app.config import get_settings
from app.database import insert_trace_step
from app.models import TraceStepType

logger = logging.getLogger(__name__)


async def tools_executer_node(state: AgentState) -> AgentState:
    """Execute the tools requested by the LLM."""
    last_message: AIMessage = state["messages"][-1]
    settings = get_settings()
    task_id = state["task_id"]
    trace_step_index = state.get("trace_step_index", 0)
    agent_iteration = state.get("agent_iteration", 0)

    tools_results: list[ToolMessage] = []
    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        tool_call_id = tool_call["id"]
        tool_func = TOOLS_MAP.get(tool_name)

        if tool_func is None:
            description = f"Tool not found: {tool_name}"
            result = json.dumps({"error": {description}})
            
            logger.warning("Tool not found: %s (task %s)", tool_name, task_id)
            # await insert_trace_step(
            #     settings.database_url,
            #     task_id,
            #     step_index=trace_step_index,
            #     type=TraceStepType.TOOL_CALL.value,
            #     tool_name=tool_name,
            #     tool_input=json.dumps(tool_args),
            #     tool_output=result,
            #     description=description,
            # )
        else:
            logger.info("Calling tool %s (task %s)", tool_name, task_id)
            try:
                result = await tool_func.ainvoke(tool_args)
                description = f"Executed {tool_name}. See trace for details."
                logger.info(
                    "Tool %s succeeded (task %s): %.120s",
                    tool_name, task_id, str(result),
                )
            except Exception as e:
                description = f"Error executing {tool_name}. See trace for details."
                result = json.dumps({"error": {description}})
                
                logger.error(
                    "Tool %s raised an exception (task %s): %s",
                    tool_name, task_id, e,
                )

        await insert_trace_step(
            settings.database_url,
            task_id,
            step_index=trace_step_index,
            type=TraceStepType.TOOL_CALL.value,
            tool_name=tool_name,
            tool_input=json.dumps(tool_args),
            tool_output=result,
            description=description,
        )
            
        tools_results.append(ToolMessage(content=result, tool_call_id=tool_call_id))

    return {
        "messages": tools_results,
        "trace_step_index": trace_step_index + 1,
        "agent_iteration": agent_iteration + 1,
    }