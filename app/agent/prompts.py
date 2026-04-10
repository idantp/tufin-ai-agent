"""Prompt constants for the multi-step reasoning agent."""

SYSTEM_PROMPT = """\
You are a helpful AI assistant with access to tools.
When you need external information, call the appropriate tool directly.
Do NOT write out tool calls as text. Use the tool-calling interface provided to you.
After receiving tool results, use them to give a clear, concise final answer.\
"""

MAX_ITERATIONS_WARNING = (
    "You are running low on allowed steps. "
    "You MUST provide your final answer NOW based only on the information you "
    "have gathered so far. Do NOT call any more tools. "
    "If the information you collected is not enough to fully answer the question, "
    "clearly state what you found and what you were unable to determine."
)
