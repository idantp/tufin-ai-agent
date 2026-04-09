"""Models for the tools."""

from pydantic import BaseModel, Field


class CalculatorOutput(BaseModel):
    """Output model for the calculator tool."""

    result: float | int | None = Field(
        default=None,
        description="The numeric result of the expression, or None if evaluation failed",
    )
    error: str | None = Field(
        default=None,
        description="Error message if evaluation failed, otherwise None",
    )


class WeatherOutput(BaseModel):
    """Output model for the weather tool."""

    city: str | None = Field(default=None, description="Normalized city name returned by the API")
    country: str | None = Field(default=None, description="Two-letter country code")
    temperature_celsius: float | None = Field(default=None, description="Current temperature in °C")
    feels_like_celsius: float | None = Field(default=None, description="Feels-like temperature in °C")
    humidity_percent: int | None = Field(default=None, description="Relative humidity in percent")
    description: str | None = Field(default=None, description="Short weather description (e.g. 'light rain')")
    wind_speed_ms: float | None = Field(default=None, description="Wind speed in metres per second")
    error: str | None = Field(default=None, description="Error message if the request failed, otherwise None")


class WebSearchOutput(BaseModel):
    """Output model for the web search tool."""

    query: str | None = Field(default=None, description="The search query that was executed")
    summary: str | None = Field(default=None, description="AI-generated summary of the search results")
    results: list[dict] | None = Field(default=None, description="List of search results with title, url, and content")
    error: str | None = Field(default=None, description="Error message if the request failed, otherwise None")

