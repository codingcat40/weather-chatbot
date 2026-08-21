# weather-chatbot

A Flask-based weather chatbot backend that resolves locations and forecasts via the free [Open-Meteo](https://open-meteo.com/) API.

## Project structure

```
backend/
  app.py          # Flask app factory, health check endpoint
  config.py       # Config (CORS origins, Open-Meteo endpoints, cache TTL)
  routes/         # Blueprint routes (chat)
  services/       # Business logic
  utils/          # Helpers
models/
  utils/cache.py  # In-memory caching utilities
frontend/         # (placeholder for the client app)
```

## Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate      # Windows
pip install -r requirements.txt
python app.py
```

## Configuration

Environment variables (optional, see `backend/config.py`):

- `CORS_ORIGINS` — comma-separated allowed origins (default `http://localhost:5173`)
- `CACHE_TTL_SECOND` — cache TTL in seconds (default `600`)
- `FLASK_DEBUG` — `1` to enable debug mode (default `1`)

No API key is required — Open-Meteo's geocoding and forecast endpoints are free and public.
