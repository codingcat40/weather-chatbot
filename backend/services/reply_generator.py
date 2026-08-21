"""Conversational reply composition.

Tries the Hugging Face free-tier Inference API (a small instruction-tuned
generative model) to turn the fetched weather data into a natural-sounding
chat reply. On ANY failure - timeout, non-200, rate limit, cold start,
malformed/empty output - falls back to a deterministic template reply.
`generate_reply` never raises; the bot must never surface a raw upstream
error to the user.

Not cached: each chat message + weather snapshot is a different prompt, so
there'd be effectively no cache hit rate - see services/cache.py.
"""

import logging
import random

import requests

from config import Config
from services.weather import WeatherResult

logger = logging.getLogger(__name__)

_INFERENCE_URL = "https://api-inference.huggingface.co/models/{model}"

_ASK_FOR_LOCATION_REPLIES = [
    "I can help with the weather — try telling me a city, region, or coordinates, like \"weather in Tokyo\" or \"40.7,-74.0\".",
    "Which location would you like the weather for? A city, province, or a lat/lon pair both work.",
    "Tell me a place (or coordinates) and I'll pull up the forecast!",
]


def canned_ask_for_location() -> str:
    return random.choice(_ASK_FOR_LOCATION_REPLIES)


def _build_prompt(user_message: str, weather: WeatherResult, location_label: str) -> str:
    forecast_lines = "\n".join(
        f"- {day.date}: {day.condition}, high {day.temp_max:.0f}°C / low {day.temp_min:.0f}°C"
        for day in weather.forecast
    )
    return (
        "Write a short, friendly, conversational reply (2-3 sentences, no lists) "
        "for a weather chat bot.\n"
        f'User asked: "{user_message}"\n'
        f"Location: {location_label}\n"
        f"Current conditions: {weather.current.temp:.0f}°C, {weather.current.condition}, "
        f"wind {weather.current.wind_speed:.0f} km/h.\n"
        f"Forecast:\n{forecast_lines}\n"
        "Reply:"
    )


def _call_generation_model(prompt: str) -> str | None:
    if not Config.HUGGINGFACE_API_TOKEN:
        return None

    url = _INFERENCE_URL.format(model=Config.HF_GENERATION_MODEL)
    headers = {"Authorization": f"Bearer {Config.HUGGINGFACE_API_TOKEN}"}
    body = {"inputs": prompt, "parameters": {"max_new_tokens": 120}}

    try:
        resp = requests.post(url, headers=headers, json=body, timeout=Config.HF_API_TIMEOUT_SECONDS)
    except requests.RequestException as exc:
        logger.warning("HF generation request failed: %s", exc)
        return None

    if resp.status_code != 200:
        logger.warning("HF generation call returned %s: %s", resp.status_code, resp.text[:200])
        return None

    data = resp.json()
    if isinstance(data, list) and data and isinstance(data[0], dict):
        text = data[0].get("generated_text")
        if text and text.strip():
            return text.strip()
    return None


def template_reply(weather: WeatherResult, location_label: str) -> str:
    """Deterministic fallback - zero external dependency, always available."""
    current = weather.current
    parts = [f"Right now in {location_label} it's {current.temp:.0f}°C and {current.condition.lower()}."]
    if len(weather.forecast) > 1:
        tomorrow = weather.forecast[1]
        parts.append(
            f"Tomorrow looks like {tomorrow.condition.lower()}, with a high of "
            f"{tomorrow.temp_max:.0f}°C and a low of {tomorrow.temp_min:.0f}°C."
        )
    return " ".join(parts)


def generate_reply(user_message: str, weather: WeatherResult, location_label: str) -> str:
    try:
        prompt = _build_prompt(user_message, weather, location_label)
        generated = _call_generation_model(prompt)
        if generated:
            return generated
    except Exception:  # noqa: BLE001 - last-resort safety net, must never propagate
        logger.exception("Unexpected error generating reply via HF; falling back to template.")

    return template_reply(weather, location_label)
