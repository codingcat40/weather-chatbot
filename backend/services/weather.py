"""Open-Meteo forecast lookups.

Fetches current conditions + a short daily forecast for a lat/lon point,
using https://open-meteo.com/en/docs (WMO weather codes -> text via
WMO_WEATHER_CODES below).
"""

from dataclasses import dataclass
from typing import Optional

import requests

from config import Config
from services.cache import TTLCache

_cache = TTLCache(Config.CACHE_TTL_SECONDS)

FORECAST_DAYS = 5

WMO_WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


class WeatherError(Exception):
    """Raised when the upstream forecast API can't be reached."""


def describe_weather_code(code: Optional[int]) -> str:
    if code is None:
        return "Unknown"
    return WMO_WEATHER_CODES.get(code, "Unknown")


@dataclass
class CurrentConditions:
    temp: float
    condition: str
    code: Optional[int]
    wind_speed: float
    humidity: Optional[float]


@dataclass
class DayForecast:
    date: str
    temp_max: float
    temp_min: float
    condition: str
    code: Optional[int]


@dataclass
class WeatherResult:
    current: CurrentConditions
    forecast: list[DayForecast]


def get_weather(latitude: float, longitude: float, timezone: str = "auto") -> WeatherResult:
    """Fetch current + forecast weather for a point."""
    cache_key = f"wx:{latitude:.4f}:{longitude:.4f}"
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "timezone": timezone,
        "current_weather": "true",
        "daily": "weathercode,temperature_2m_max,temperature_2m_min",
        "forecast_days": FORECAST_DAYS,
    }
    try:
        resp = requests.get(Config.FORECAST_API_URL, params=params, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise WeatherError(str(exc)) from exc

    data = resp.json()
    current_raw = data.get("current_weather") or {}
    daily = data.get("daily") or {}
    dates = daily.get("time") or []
    codes = daily.get("weathercode") or []
    highs = daily.get("temperature_2m_max") or []
    lows = daily.get("temperature_2m_min") or []

    current_code = current_raw.get("weathercode")
    current = CurrentConditions(
        temp=current_raw.get("temperature"),
        condition=describe_weather_code(current_code),
        code=current_code,
        wind_speed=current_raw.get("windspeed"),
        humidity=None,
    )

    forecast = [
        DayForecast(
            date=dates[i],
            temp_max=highs[i],
            temp_min=lows[i],
            condition=describe_weather_code(codes[i]),
            code=codes[i],
        )
        for i in range(min(len(dates), len(codes), len(highs), len(lows)))
    ]

    result = WeatherResult(current=current, forecast=forecast)
    _cache.set(cache_key, result)
    return result
