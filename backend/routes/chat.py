import logging

from flask import Blueprint, jsonify, request

from services.geocoding import GeocodingError, LocationNotFoundError, resolve_location
from services.nlu import extract_location_text
from services.reply_generator import canned_ask_for_location, generate_reply
from services.weather import WeatherError, get_weather
from utils.coords import extract_coordinates
from utils.responses import build_chat_response, build_error_response, build_weather_card

logger = logging.getLogger(__name__)

chat_bp = Blueprint("chat", __name__, url_prefix="/api")


@chat_bp.route("/chat", methods=["POST"])
def chat():
    body = request.get_json(silent=True) or {}
    message = (body.get("message") or "").strip()

    if not message:
        return jsonify(build_error_response("EMPTY_MESSAGE", "Say something and I'll look up the weather!")), 400

    try:
        return jsonify(_handle_message(message))
    except Exception:  # noqa: BLE001 - last-resort safety net, never a bodiless 500
        logger.exception("Unhandled error in /api/chat")
        return jsonify(build_chat_response(
            reply="Something went wrong on my end — please try again.",
            source="error",
        )), 200


def _handle_message(message: str) -> dict:
    coords = extract_coordinates(message)
    if coords:
        lat, lon = coords
        location_label = f"{lat:.4f}, {lon:.4f}"
    else:
        location_text = extract_location_text(message)
        if not location_text:
            return build_chat_response(canned_ask_for_location(), source="canned")

        try:
            resolved = resolve_location(location_text)
        except LocationNotFoundError:
            return build_chat_response(
                f'I couldn\'t find a place called "{location_text}".', source="not_found"
            )
        except GeocodingError:
            logger.warning("Geocoding upstream failure for query=%r", location_text)
            return build_chat_response(
                "I'm having trouble looking up locations right now — please try again shortly.",
                source="error",
            )

        lat, lon = resolved.latitude, resolved.longitude
        location_label = resolved.label

    try:
        weather = get_weather(lat, lon)
    except WeatherError:
        logger.warning("Weather upstream failure for lat=%s lon=%s", lat, lon)
        return build_chat_response(
            "I found the location but couldn't fetch the weather right now — please try again shortly.",
            source="error",
        )

    reply_text = generate_reply(message, weather, location_label)
    card = build_weather_card(location_label, weather)
    return build_chat_response(reply_text, card=card, source="weather")
