# Weather Chatbot — Implementation Plan

## 1. Overview

A chat interface where users interact via **slash commands** instead of free text:

- User types `/` → a dropdown appears with options: `city`, `country`, `province`
- User picks a type and types a name, e.g. `/city Tokyo`
- The Flask backend resolves the name to coordinates via the **Open-Meteo Geocoding API**, fetches current + forecast weather from the **Open-Meteo Forecast API**, and returns a chat-style reply
- The React frontend renders the reply as a bot message bubble containing a weather card

**Tech stack**

| Layer | Tech |
|---|---|
| Backend | Flask, flask-cors, requests, python-dotenv |
| Frontend | React + TypeScript (Vite) |
| Weather data | Open-Meteo API — free, no API key (Geocoding + Forecast endpoints) |

No API key management, no database — everything is a stateless request/response plus an in-memory cache.

---

## 2. Current State Audit

The repo already has a scaffold. What exists vs. what's missing:

**Exists (backend):**
- `backend/app.py` — Flask app factory, registers `chat_bp`, has `GET /api/health`
- `backend/config.py` — `Config` class with `CORS_ORIGINS`, Open-Meteo URLs, `CACHE_TTL_SECONDS`, `DEBUG`
  - ⚠️ Bug: `FORECAST_API_KEY` is actually a **URL**, should be named `FORECAST_API_URL`
- `backend/routes/chat.py` — placeholder `POST /api/chat` that just echoes a static reply
- `backend/services/__init__.py`, `backend/utils/__init__.py` — empty packages, no logic yet
- `backend/requirements.txt` — Flask, flask-cors, requests, python-dotenv (sufficient, no changes needed)

**Exists but misplaced:**
- `models/utils/cache.py` — empty file, sitting outside `backend/` entirely. To be removed; its purpose is absorbed by `backend/services/cache.py`.

**Missing entirely:**
- All backend service/business logic (geocoding lookup, forecast lookup, caching, command parsing, response formatting)
- The entire `frontend/` app — no Vite scaffold, no `package.json`, no components exist yet
- No `.env` / `.env.example`
- No `README.md` with setup instructions
- No git repo initialized

---

## 3. Architecture

### 3.1 Backend

Keep the existing app-factory + blueprint pattern. Add these modules:

```
backend/
  app.py                      (existing — no structural change)
  config.py                   (fix FORECAST_API_KEY -> FORECAST_API_URL)
  routes/
    chat.py                   (existing — wire up to services)
  services/
    geocoding.py              (new — Open-Meteo geocoding lookup)
    weather.py                (new — Open-Meteo forecast lookup)
    cache.py                  (new — simple TTL in-memory cache)
  utils/
    command_parser.py         (new — parses "/city Tokyo" -> {type, query})
    formatter.py               (new — builds chat reply text + weather card JSON)
  .env.example                (new)
```

Remove `models/utils/cache.py` and the stray `models/` directory (its job is done by `backend/services/cache.py`).

**Command-type resolution nuance:** Open-Meteo's geocoding index (GeoNames-based) covers populated places *and* administrative regions, so `/city`, `/country`, and `/province` all hit the same `geocoding-api.open-meteo.com/v1/search` endpoint — but naive "first result" isn't good enough for `/country` or `/province`:
- `/city <name>` → search, prefer highest-population populated-place match
- `/province <name>` → search, prefer a result whose `feature_code` indicates an admin1-level region, or whose `admin1` field matches the query
- `/country <name>` → search, prefer the result whose `country` field matches and which represents the capital/largest city (Open-Meteo's forecast API needs a lat/lon point, so a country resolves to its most representative city)

This picking logic lives in `services/geocoding.py`, parameterized by the command type.

**API contract**

`POST /api/chat`
```jsonc
// Request
{ "message": "/city Tokyo" }

// Success response
{
  "reply": "Here's the weather for Tokyo, Japan:",
  "card": {
    "location": "Tokyo",
    "country": "Japan",
    "current": { "temp": 27.4, "condition": "Partly cloudy", "wind": 12.1, "humidity": 60 },
    "forecast": [
      { "date": "2026-08-22", "tempMax": 29, "tempMin": 23, "condition": "Sunny" }
    ]
  }
}

// Error response
{ "reply": "I couldn't find a city called \"Atlantis\".", "error": "NOT_FOUND" }
```

`GET /api/health` — unchanged, already works.

### 3.2 Frontend

Scaffold from scratch with Vite (`npm create vite@latest frontend -- --template react-ts`):

```
frontend/
  src/
    api/chat.ts               (POST /api/chat client)
    components/
      ChatWindow.tsx           (message list container)
      MessageBubble.tsx        (user / bot bubble)
      WeatherCard.tsx          (renders the `card` payload)
      SlashCommandInput.tsx    (input box; shows dropdown of city/country/province on "/")
    App.tsx
    main.tsx
  .env.example                 (VITE_API_BASE_URL)
```

`SlashCommandInput` behavior:
1. User types `/` → dropdown shows `city`, `country`, `province`
2. User selects one → input becomes `/city ` and awaits the name
3. On submit, sends `{ message: "/city Tokyo" }` to the backend, appends a user bubble, then a bot bubble once the response returns

---

## 4. Features

### MVP (Phase 1)
- Slash command dropdown for `/city`, `/country`, `/province`
- Backend geocoding resolution for all three types (with the picking strategy above)
- Current weather + short (3–5 day) forecast in the response
- Chat-style UI: user bubble + bot bubble with an embedded weather card
- Error handling: location not found, upstream API failure/timeout, malformed command
- In-memory TTL cache (`CACHE_TTL_SECONDS`, already in `Config`) keyed by `type:query` to avoid redundant Open-Meteo calls
- CORS restricted to the Vite dev origin (`CORS_ORIGINS`, already in `Config`)

### Stretch (Phase 2)
- Autocomplete-as-you-type city suggestions (debounced geocoding calls while typing)
- °C/°F unit toggle
- Disambiguation UI when geocoding returns multiple plausible matches (e.g. multiple cities named "Springfield")
- Chat history persisted to `localStorage`
- Typing/loading indicator while awaiting the backend response
- Dark mode
- Dockerfile(s) + basic deploy notes (e.g. Render for backend, Vercel/Netlify for frontend)

---

## 5. Step-by-Step Roadmap

**Backend**
1. Fix `Config.FORECAST_API_KEY` → `FORECAST_API_URL` in `backend/config.py`
2. Delete the stray `models/` directory
3. Implement `backend/services/cache.py` — simple TTL dict cache with `get`/`set`
4. Implement `backend/services/geocoding.py` — calls Open-Meteo geocoding, applies per-type result-picking logic
5. Implement `backend/services/weather.py` — calls Open-Meteo forecast given lat/lon, returns current + forecast data
6. Implement `backend/utils/command_parser.py` — parses/validates raw message into `{type, query}`, rejects unknown types or empty queries
7. Implement `backend/utils/formatter.py` — builds the `reply` string + `card` JSON from weather data
8. Wire `backend/routes/chat.py`: parse → geocode (cache-checked) → fetch weather (cache-checked) → format → return JSON; return proper error shapes/status codes for bad input, not-found, upstream failures
9. Add `backend/.env.example` documenting `CORS_ORIGINS`, `CACHE_TTL_SECONDS`, `FLASK_DEBUG`
10. Manually test the backend in isolation (see Verification)

**Frontend**
11. Scaffold Vite React-TS app in `frontend/`
12. Build `SlashCommandInput` with the `/` dropdown and command composition
13. Build `ChatWindow`, `MessageBubble`, `WeatherCard`
14. Build `api/chat.ts` to call `POST /api/chat`, handle loading/error states
15. Wire everything together in `App.tsx`; basic CSS styling for the chat layout and card
16. End-to-end manual test against the running backend

**Wrap-up**
17. Add root `README.md` with setup/run instructions for both backend and frontend
18. (Optional) `git init` + initial commit
19. Tackle Phase 2 stretch features as time allows

---

## 6. Verification

**Backend (once implemented), from `backend/`:**
```bash
python -m venv venv && venv\Scripts\activate   # if not already set up
pip install -r requirements.txt
python -c "from app import create_app; create_app().run(debug=True)"
```
Then:
```bash
curl -X POST http://localhost:5000/api/chat -H "Content-Type: application/json" -d "{\"message\": \"/city Tokyo\"}"
curl -X POST http://localhost:5000/api/chat -H "Content-Type: application/json" -d "{\"message\": \"/country Japan\"}"
curl -X POST http://localhost:5000/api/chat -H "Content-Type: application/json" -d "{\"message\": \"/province Ontario\"}"
curl -X POST http://localhost:5000/api/chat -H "Content-Type: application/json" -d "{\"message\": \"/city Atlantis\"}"   # expect NOT_FOUND
curl -X POST http://localhost:5000/api/chat -H "Content-Type: application/json" -d "{\"message\": \"hello\"}"           # expect parse error
curl http://localhost:5000/api/health
```

**Frontend (once scaffolded), from `frontend/`:**
```bash
npm install
npm run dev
```
Then in the browser: type `/`, confirm the dropdown appears; select each of `city`/`country`/`province`, submit a valid and an invalid name, confirm the bot bubble + weather card render correctly and errors display gracefully.
