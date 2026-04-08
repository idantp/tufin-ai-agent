"""
Web search tool for searching the web and returning summarized results.

Uses the Tavily API with the key configured via TAVILY_API_KEY in the
application settings.
"""

import logging

from pydantic import BaseModel, Field
from tavily import TavilyClient

from app.config import get_settings


logger = logging.getLogger(__name__)

_REQUEST_TIMEOUT = 10.0


class WebSearchInput(BaseModel):
    """Input model for the web search tool."""

    query: str = Field(
        min_length=1,
        max_length=500,
        description="Search query to find information on the web (e.g. 'latest AI developments')",
    )
    max_results: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Maximum number of search results to return (1-10)",
    )


class WebSearchOutput(BaseModel):
    """Output model for the web search tool."""

    query: str | None = Field(default=None, description="The search query that was executed")
    summary: str | None = Field(default=None, description="AI-generated summary of the search results")
    results: list[dict] | None = Field(default=None, description="List of search results with title, url, and content")
    error: str | None = Field(default=None, description="Error message if the request failed, otherwise None")


async def search_web(input: WebSearchInput) -> WebSearchOutput:
    """
    Search the web using Tavily and return summarized results.

    Args:
        input: WebSearchInput containing the search query and max results.

    Returns:
        WebSearchOutput with search results and summary, or an error message on failure.
    """
    settings = get_settings()

    if not settings.tavily_api_key:
        logger.warning("Tavily API key is not configured")
        return WebSearchOutput(error="Tavily API key is not configured")

    logger.debug("Searching web for query: %s (max_results=%d)", input.query, input.max_results)

    try:
        client = TavilyClient(api_key=settings.tavily_api_key)
        
        response = client.search(
            query=input.query,
            max_results=input.max_results,
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
            query=input.query,
            summary=summary,
            results=results,
        )

        logger.debug(
            "Web search completed: query='%s' | results=%d | summary_length=%d",
            input.query,
            len(results),
            len(summary) if summary else 0,
        )
        return result

    except Exception as exc:
        logger.warning("Error searching web for query: %s | error: %s", input.query, exc)
        return WebSearchOutput(error=f"Search error: {exc}")
