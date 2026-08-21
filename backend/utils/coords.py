"""Fast-path detection of raw "lat,lon" coordinates typed in free text.

Runs before any NLU/model call - if the user already gave us coordinates
(e.g. "weather at 40.7128, -74.0060" or "40.7,-74.0"), there's no need to
spend a Hugging Face call on it.
"""

import re
from typing import Optional

_COORD_PATTERN = re.compile(
    r"(-?\d{1,3}\.\d+)\s*[,]\s*(-?\d{1,3}\.\d+)"
)


def extract_coordinates(text: str) -> Optional[tuple[float, float]]:
    """Return (lat, lon) if a valid coordinate pair is found in `text`, else None.

    Requires decimal points and a comma separator to avoid false positives
    on plain numbers in a sentence (e.g. "in 20 minutes"), and validates
    that the values fall within real latitude/longitude ranges.
    """
    match = _COORD_PATTERN.search(text)
    if not match:
        return None

    lat, lon = float(match.group(1)), float(match.group(2))
    if -90 <= lat <= 90 and -180 <= lon <= 180:
        return lat, lon
    return None
