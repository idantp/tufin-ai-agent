"""
Web search tool for searching the web and returning summarized results.

Uses the Tavily API with the key configured via TAVILY_API_KEY in the
application settings.
"""

import asyncio
import logging

from tavily import TavilyClient

from app.config import get_settings
from app.tools.models import WebSearchOutput
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

_REQUEST_TIMEOUT = 10.0



@tool
async def search_web(query: str, max_results: int = 3) -> str:
    """
    Search the web and return a summarized answer. Use this to look up any factual information.

    Args:
        query: Search query (e.g. "latest AI developments").
        max_results: Maximum number of results to return (1-10). Defaults to 3.
    """
    settings = get_settings()

    if not settings.tavily_api_key:
        logger.warning("Tavily API key is not configured")
        return WebSearchOutput(error="Tavily API key is not configured").model_dump_json()

    logger.debug("Searching web for query: %s (max_results=%d)", query, max_results)

    try:
        client = TavilyClient(api_key=settings.tavily_api_key)

        response = await asyncio.to_thread(
            client.search,
            query=query,
            max_results=max_results,
            include_answer=True,
        )

        results = []
        for item in response.get("results", []):
            results.append({
                "title": item.get("title"),
                "url": item.get("url"),
                "content": item.get("content"),
            })

        summary = response.get("answer", "No summary available")

        result = WebSearchOutput(
            summary=summary,
        ).model_dump_json()

        logger.debug(
            "Web search completed: query='%s' | results=%d | summary_length=%d",
            query,
            len(results),
            len(summary) if summary else 0,
        )
        return result

    except Exception as exc:
        logger.warning("Error searching web for query: %s | error: %s", query, exc)
        return WebSearchOutput(error=f"Search error: {exc}").model_dump_json()
