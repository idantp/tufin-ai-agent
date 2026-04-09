"""LLM for the agent."""

from langchain_core.language_models import BaseChatModel
from langchain_ollama import ChatOllama
from app.config import get_settings
from app.tools import calculate, get_weather, search_web

ALL_TOOLS = [calculate, get_weather, search_web]

def get_llm_with_tools() -> BaseChatModel:
    """Get an LLM with tools.
    
    Returns:
        BaseChatModel: The LLM with tools.
    """
    settings = get_settings()
    llm = ChatOllama(model=settings.ollama_model, base_url=settings.ollama_base_url, temperature=0.0)
    return llm.bind_tools(ALL_TOOLS)

LLM_WITH_TOOLS = get_llm_with_tools()
TOOLS_MAP = {tool.name: tool for tool in ALL_TOOLS}
