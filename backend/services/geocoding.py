"""Open-Meteo geocoding lookups.

Resolves a free-text location string (city / country / province / anything
in between - the NLU layer only hands us a bare name, not a type) to a
lat/lon point plus display metadata, using
https://open-meteo.com/en/docs/geocoding-api.

Open-Meteo's GeoNames-based index is patchy for well-known provinces/states
(see services/known_regions.py for the curated fallback used first). For
everything else, a generic name search is issued and the candidates are
ranked by `feature_code` so that e.g. a capital/major city wins over an
obscure same-named hamlet.
"""

from dataclasses import dataclass
from typing import Optional

import requests

from config import Config
from services.cache import TTLCache
from services.known_regions import KNOWN_PROVINCES

_cache = TTLCache(Config.CACHE_TTL_SECONDS)

# Best point to represent a location -> lowest rank number wins.
_FEATURE_CODE_RANK = {
    "PPLC": 0,  # capital city
    "PPLA": 1,  # first-order admin division seat
    "PPLA2": 2,  # second-order admin division seat
    "PPL": 3,  # populated place
    "ADM1": 4,  # first-order admin division (province/state) itself
    "PCLI": 5,  # independent country
}
_DEFAULT_RANK = 9

_COUNTRY_CODE_NAMES = {"CA": "Canada", "US": "United States"}


class GeocodingError(Exception):
    """Raised when the upstream geocoding API can't be reached."""


class LocationNotFoundError(Exception):
    """Raised when no matching location is found for the query."""


@dataclass
class ResolvedLocation:
    name: str
    admin1: Optional[str]
    country: Optional[str]
    latitude: float
    longitude: float

    @property
    def label(self) -> str:
        return f"{self.name}, {self.country}" if self.country else self.name


def _search(name: str, *, count: int = 10, country_code: Optional[str] = None) -> list[dict]:
    params = {"name": name, "count": count, "language": "en", "format": "json"}
    if country_code:
        params["countryCode"] = country_code
    try:
        resp = requests.get(Config.GEOCODING_API_URL, params=params, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise GeocodingError(str(exc)) from exc
    return resp.json().get("results") or []


def _pick_best(results: list[dict]) -> dict:
    return min(
        results,
        key=lambda r: (
            _FEATURE_CODE_RANK.get(r.get("feature_code", ""), _DEFAULT_RANK),
            -(r.get("population") or 0),
        ),
    )


def _resolve_known_province(capital: str, country_code: str) -> Optional[dict]:
    """Resolve a known province/state by geocoding its capital, scoped to
    the right country via `countryCode` - see services/known_regions.py."""
    results = _search(capital, count=1, country_code=country_code)
    return results[0] if results else None


def resolve_location(query: str) -> ResolvedLocation:
    """Resolve `query` to a location: {name, admin1, country, lat, lon}.

    Raises LocationNotFoundError if nothing matches, GeocodingError if the
    upstream API request fails.
    """
    normalized = query.strip().lower()
    cache_key = f"geo:{normalized}"
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    known = KNOWN_PROVINCES.get(normalized)
    if known:
        capital, country_code = known
        match = _resolve_known_province(capital, country_code)
        if match:
            resolved = ResolvedLocation(
                name=query.strip().title(),
                admin1=None,
                country=_COUNTRY_CODE_NAMES.get(country_code, country_code),
                latitude=match["latitude"],
                longitude=match["longitude"],
            )
            _cache.set(cache_key, resolved)
            return resolved
        # Fall through to a generic search if the capital lookup somehow failed.

    results = _search(query)
    if not results:
        raise LocationNotFoundError(query)

    best = _pick_best(results)
    resolved = ResolvedLocation(
        name=best.get("name", query),
        admin1=best.get("admin1"),
        country=best.get("country"),
        latitude=best["latitude"],
        longitude=best["longitude"],
    )
    _cache.set(cache_key, resolved)
    return resolved
