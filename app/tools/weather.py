import httpx
from typing import Any

WTTR_URL = "https://wttr.in/{city}?format=j1"


def get_weather(city: str) -> dict[str, Any]:
    """
    Fetch current weather for a given city using wttr.in.
    No API key required.

    Args:
        city: City name e.g. "Paris", "New York", "Tel Aviv"

    Returns:
        Dict with current weather conditions or an error message.
    """
    try:
        response = httpx.get(
            WTTR_URL.format(city=city),
            timeout=10,
            follow_redirects=True,
        )
        response.raise_for_status()
        data = response.json()

        current = data["current_condition"][0]


        return {
            "city": city,
            "temp_celsius": int(current["temp_C"]),
            "feels_like_celsius": int(current["FeelsLikeC"]),
            "description": current["weatherDesc"][0]["value"],
            "humidity_percentage": int(current["humidity"]),
            "precipitation_mm": float(current["precipMM"]),
        }

    # TODO: Handle the errors properly
    except httpx.TimeoutException:
        return {"error": f"Request timed out fetching weather for '{city}'"}
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP {e.response.status_code} fetching weather for '{city}'"}
    except (KeyError, IndexError, ValueError) as e:
        return {"error": f"Unexpected response format from weather API: {e}"}
    except Exception as e:
        return {"error": f"Unexpected error: {e}"}