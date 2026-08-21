"""Simple in-memory TTL cache.

Not shared across processes/workers and not persisted - good enough for a
single dev/small deployment to avoid hammering the Open-Meteo API for
repeated lookups within a short window. Not used for Hugging Face calls:
each chat message is different free text, so the cache-key cardinality is
effectively unbounded and the hit rate would be ~0 - it wouldn't earn its
complexity.
"""

import time
import threading
from typing import Any, Optional


class TTLCache:
    def __init__(self, ttl_seconds: int):
        self._ttl_seconds = ttl_seconds
        self._lock = threading.Lock()
        self._store: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            expires_at, value = entry
            if expires_at < time.monotonic():
                del self._store[key]
                return None
            return value

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._store[key] = (time.monotonic() + self._ttl_seconds, value)
