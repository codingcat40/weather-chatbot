import os

class Config:
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")
    
    # open meteo endpoints
    GEOCODING_API_URL = "https://geocoding-api.open-meteo.com/v1/search"
    FORECAST_API_KEY = "https://api.open-meteo.com/v1/forecast"
    
    # in memory cache (seconds)
    CACHE_TTL_SECONDS = int(os.environ.get("CACHE_TTL_SECOND", "600"))
    DEBUG = os.environ.get("FLASK_DEBUG", "1") == "1"
    
    