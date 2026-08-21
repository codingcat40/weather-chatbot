import pytest

from app import create_app
from services.geocoding import LocationNotFoundError, ResolvedLocation
from services.weather import CurrentConditions, DayForecast, WeatherError, WeatherResult


@pytest.fixture
def client():
    app = create_app()
    app.testing = True
    return app.test_client()


def _fake_weather():
    return WeatherResult(
        current=CurrentConditions(temp=22.0, condition="Partly cloudy", code=2, wind_speed=14.0, humidity=None),
        forecast=[
            DayForecast(date="2026-08-21", temp_max=24.0, temp_min=16.0, condition="Partly cloudy", code=2),
            DayForecast(date="2026-08-22", temp_max=23.0, temp_min=15.0, condition="Sunny", code=0),
        ],
    )


def test_chat_with_coordinates_returns_weather_card(client, monkeypatch):
    monkeypatch.setattr("routes.chat.get_weather", lambda lat, lon: _fake_weather())
    monkeypatch.setattr("routes.chat.generate_reply", lambda *a, **k: "It's a nice day.")

    resp = client.post("/api/chat", json={"message": "weather at 40.7128, -74.0060"})
    data = resp.get_json()

    assert resp.status_code == 200
    assert data["reply"] == "It's a nice day."
    assert data["card"]["location"] == "40.7128, -74.0060"
    assert data["card"]["current"]["temp"] == 22.0
    assert len(data["card"]["forecast"]) == 2


def test_chat_with_place_name_resolves_location(client, monkeypatch):
    monkeypatch.setattr("routes.chat.extract_location_text", lambda msg: "Tokyo")
    monkeypatch.setattr(
        "routes.chat.resolve_location",
        lambda query: ResolvedLocation(name="Tokyo", admin1=None, country="Japan", latitude=35.6, longitude=139.7),
    )
    monkeypatch.setattr("routes.chat.get_weather", lambda lat, lon: _fake_weather())
    monkeypatch.setattr("routes.chat.generate_reply", lambda *a, **k: "Sunny in Tokyo.")

    resp = client.post("/api/chat", json={"message": "what's the weather in Tokyo"})
    data = resp.get_json()

    assert resp.status_code == 200
    assert data["card"]["location"] == "Tokyo, Japan"


def test_chat_with_no_location_found_returns_canned_reply(client, monkeypatch):
    monkeypatch.setattr("routes.chat.extract_location_text", lambda msg: None)

    resp = client.post("/api/chat", json={"message": "hello there"})
    data = resp.get_json()

    assert resp.status_code == 200
    assert data["card"] is None
    assert data["reply"]


def test_chat_with_unresolvable_location_returns_not_found_reply(client, monkeypatch):
    monkeypatch.setattr("routes.chat.extract_location_text", lambda msg: "Qwxzplace")

    def raise_not_found(query):
        raise LocationNotFoundError(query)

    monkeypatch.setattr("routes.chat.resolve_location", raise_not_found)

    resp = client.post("/api/chat", json={"message": "weather in Qwxzplace"})
    data = resp.get_json()

    assert resp.status_code == 200
    assert "Qwxzplace" in data["reply"]
    assert data["card"] is None


def test_chat_with_weather_upstream_failure_degrades_gracefully(client, monkeypatch):
    monkeypatch.setattr("routes.chat.extract_location_text", lambda msg: "Tokyo")
    monkeypatch.setattr(
        "routes.chat.resolve_location",
        lambda query: ResolvedLocation(name="Tokyo", admin1=None, country="Japan", latitude=35.6, longitude=139.7),
    )

    def raise_weather_error(lat, lon):
        raise WeatherError("upstream down")

    monkeypatch.setattr("routes.chat.get_weather", raise_weather_error)

    resp = client.post("/api/chat", json={"message": "weather in Tokyo"})
    data = resp.get_json()

    assert resp.status_code == 200
    assert data["card"] is None
    assert data["reply"]


def test_chat_with_empty_message_returns_400(client):
    resp = client.post("/api/chat", json={"message": "   "})
    data = resp.get_json()

    assert resp.status_code == 400
    assert data["error"] == "EMPTY_MESSAGE"
