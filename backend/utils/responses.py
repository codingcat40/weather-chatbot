"""Helpers to build the standard /api/chat JSON envelope."""

from services.weather import WeatherResult


def build_chat_response(reply: str, card: dict | None = None, source: str = "generated") -> dict:
    return {"reply": reply, "card": card, "meta": {"source": source}}


def build_error_response(code: str, message: str) -> dict:
    return {"reply": message, "card": None, "error": code}


def build_weather_card(location_label: str, weather: WeatherResult) -> dict:
    return {
        "location": location_label,
        "current": {
            "temp": weather.current.temp,
            "condition": weather.current.condition,
            "windSpeed": weather.current.wind_speed,
            "code": weather.current.code,
        },
        "forecast": [
            {
                "date": day.date,
                "tempMax": day.temp_max,
                "tempMin": day.temp_min,
                "condition": day.condition,
                "code": day.code,
            }
            for day in weather.forecast
        ],
    }
