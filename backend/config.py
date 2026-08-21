import os


class Config:
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")

    # Open-Meteo endpoints (free, no API key required)
    GEOCODING_API_URL = os.environ.get(
        "GEOCODING_API_URL", "https://geocoding-api.open-meteo.com/v1/search"
    )
    FORECAST_API_URL = os.environ.get(
        "FORECAST_API_URL", "https://api.open-meteo.com/v1/forecast"
    )

    # In-memory TTL cache (seconds) for geocoding + forecast lookups
    CACHE_TTL_SECONDS = int(os.environ.get("CACHE_TTL_SECONDS", "600"))

    DEBUG = os.environ.get("FLASK_DEBUG", "1") == "1"

    # Hugging Face free-tier Inference API
    HUGGINGFACE_API_TOKEN = os.environ.get("HUGGINGFACE_API_TOKEN", "")
    HF_NER_MODEL = os.environ.get("HF_NER_MODEL", "dslim/bert-base-NER")
    HF_GENERATION_MODEL = os.environ.get("HF_GENERATION_MODEL", "google/flan-t5-large")
    HF_API_TIMEOUT_SECONDS = int(os.environ.get("HF_API_TIMEOUT_SECONDS", "10"))
