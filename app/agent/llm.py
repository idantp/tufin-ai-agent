"""LLM for the agent."""

import logging

from langchain_core.language_models import BaseChatModel
from langchain_ollama import ChatOllama
from app.config import get_settings
from app.tools import calculate, get_weather, search_web

logger = logging.getLogger(__name__)


def _get_available_tools() -> list:
    settings = get_settings()
    tools = [calculate]
    if settings.tavily_api_key:
        tools.append(search_web)
    else:
        logger.warning("%s tool disabled: TAVILY_API_KEY is not configured. Please set it in your environment variables.", search_web.name)
    if settings.openweather_api_key:
        tools.append(get_weather)
    else:
        logger.warning("%s tool disabled: OPENWEATHER_API_KEY is not configured. Please set it in your environment variables.", get_weather.name)
    return tools


def _build_llm() -> ChatOllama:
    settings = get_settings()
    return ChatOllama(model=settings.ollama_model, base_url=settings.ollama_base_url, temperature=0.0, keep_alive=-1)


def get_llm_with_tools() -> BaseChatModel:
    """Get an LLM with tools.

    Returns:
        BaseChatModel: The LLM with tools.
    """
    return _build_llm().bind_tools(ALL_TOOLS)


ALL_TOOLS = _get_available_tools()
LLM = _build_llm()
LLM_WITH_TOOLS = get_llm_with_tools()
TOOLS_MAP = {tool.name: tool for tool in ALL_TOOLS}
