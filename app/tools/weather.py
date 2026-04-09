"""
Weather tool for fetching current weather conditions for a given city.

Uses the OpenWeatherMap /data/2.5/weather API with the key configured
via OPENWEATHER_API_KEY in the application settings.
"""

import logging

import httpx

from app.config import get_settings
from app.tools.models import WeatherInput, WeatherOutput
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

_OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
_REQUEST_TIMEOUT = 10.0





@tool
async def get_weather(input: WeatherInput) -> str:
    """
    Fetch current weather conditions for a city from OpenWeatherMap.

    Args:
        input: WeatherInput containing the city name (e.g. "New York", "Paris", "Tokyo").

    Returns JSON string with:
        - "city": the name of the city
        - "country": the country code
        - "temperature_celsius": the temperature in Celsius
        - "feels_like_celsius": the feels-like temperature in Celsius
        - "humidity_percent": the humidity in percent
        - "description": the weather description
        - "wind_speed_ms": the wind speed in meters per second
        - "error": the error message if the request failed, otherwise None
    """
    settings = get_settings()

    if not settings.openweather_api_key:
        logger.warning("OpenWeatherMap API key is not configured")
        return WeatherOutput(error="OpenWeatherMap API key is not configured").model_dump_json()

    logger.debug("Fetching weather for city: %s", input.city)

    try:
        async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT) as client:
            response = await client.get(
                _OPENWEATHER_URL,
                params={"q": input.city, "appid": settings.openweather_api_key, "units": "metric"},
            )

        if response.status_code == 401:
            logger.warning("Invalid OpenWeatherMap API key")
            return WeatherOutput(error="Invalid or missing OpenWeatherMap API key").model_dump_json()

        if response.status_code == 404:
            logger.warning("City not found: %s", input.city)
            return WeatherOutput(error=f"City not found: {input.city}").model_dump_json()

        if response.status_code != 200:
            logger.warning("Unexpected HTTP %s for city: %s", response.status_code, input.city)
            return WeatherOutput(error=f"Unexpected error: HTTP {response.status_code}").model_dump_json()

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
        ).model_dump_json()

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
        return WeatherOutput(error=f"Request timed out fetching weather for '{input.city}'").model_dump_json()

    except httpx.RequestError as exc:
        logger.warning("Network error fetching weather for city: %s | error: %s", input.city, exc)
        return WeatherOutput(error=f"Network error: {exc}").model_dump_json()
