"""
Weather tool for fetching current weather conditions for a given city.

Uses the OpenWeatherMap /data/2.5/weather API with the key configured
via OPENWEATHER_API_KEY in the application settings.
"""

import logging

import httpx
from pydantic import BaseModel, Field

from app.config import get_settings


logger = logging.getLogger(__name__)

_OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
_REQUEST_TIMEOUT = 10.0


class WeatherInput(BaseModel):
    """Input model for the weather tool."""

    city: str = Field(
        min_length=1,
        max_length=100,
        description="Name of the city to fetch weather for (e.g. 'London')",
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


async def get_weather(input: WeatherInput) -> WeatherOutput:
    """
    Fetch current weather conditions for a city from OpenWeatherMap.

    Args:
        input: WeatherInput containing the city name.

    Returns:
        WeatherOutput with current conditions, or an error message on failure.
    """
    settings = get_settings()

    if not settings.openweather_api_key:
        logger.warning("OpenWeatherMap API key is not configured")
        return WeatherOutput(error="OpenWeatherMap API key is not configured")

    logger.debug("Fetching weather for city: %s", input.city)

    try:
        async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT) as client:
            response = await client.get(
                _OPENWEATHER_URL,
                params={"q": input.city, "appid": settings.openweather_api_key, "units": "metric"},
            )

        if response.status_code == 401:
            logger.warning("Invalid OpenWeatherMap API key")
            return WeatherOutput(error="Invalid or missing OpenWeatherMap API key")

        if response.status_code == 404:
            logger.warning("City not found: %s", input.city)
            return WeatherOutput(error=f"City not found: {input.city}")

        if response.status_code != 200:
            logger.warning("Unexpected HTTP %s for city: %s", response.status_code, input.city)
            return WeatherOutput(error=f"Unexpected error: HTTP {response.status_code}")

        data = response.json()
        weather = data.get("weather", [{}])[0]

        result = WeatherOutput(
            city=data.get("name"),
            country=data.get("sys", {}).get("country"),
            temperature_celsius=data.get("main", {}).get("temp"),
            feels_like_celsius=data.get("main", {}).get("feels_like"),
            humidity_percent=data.get("main", {}).get("humidity"),
            description=weather.get("description"),
            wind_speed_ms=data.get("wind", {}).get("speed"),
        )

        logger.debug(
            "Weather fetched: %s, %s | temp=%.1f°C | %s",
            result.city,
            result.country,
            result.temperature_celsius or 0.0,
            result.description,
        )
        return result

    except httpx.TimeoutException:
        logger.warning("Request timed out fetching weather for city: %s", input.city)
        return WeatherOutput(error=f"Request timed out fetching weather for '{input.city}'")

    except httpx.RequestError as exc:
        logger.warning("Network error fetching weather for city: %s | error: %s", input.city, exc)
        return WeatherOutput(error=f"Network error: {exc}")
