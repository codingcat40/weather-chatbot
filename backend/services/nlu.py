"""Location extraction from free text via the Hugging Face free-tier
Inference API (NER model).

Only invoked when utils.coords.extract_coordinates found nothing - this is
the "does the message mention a place name" fallback. The free tier is
flaky (cold starts, rate limits, occasional model-loading delays), so every
failure mode here degrades to `None` rather than raising; the route layer
then falls back to a canned "ask for a location" reply.
"""

import logging
from typing import Optional

import requests

from config import Config

logger = logging.getLogger(__name__)

_INFERENCE_URL = "https://api-inference.huggingface.co/models/{model}"


def _clean_label(entity: dict) -> str:
    label = entity.get("entity_group") or entity.get("entity") or ""
    return label.split("-")[-1]  # strips a leading "B-"/"I-" (BIO tagging)


def _call_ner(message: str) -> list[dict]:
    if not Config.HUGGINGFACE_API_TOKEN:
        logger.warning("HUGGINGFACE_API_TOKEN not set - skipping NER call.")
        return []

    url = _INFERENCE_URL.format(model=Config.HF_NER_MODEL)
    headers = {"Authorization": f"Bearer {Config.HUGGINGFACE_API_TOKEN}"}
    body = {"inputs": message, "parameters": {"aggregation_strategy": "simple"}}

    try:
        resp = requests.post(url, headers=headers, json=body, timeout=Config.HF_API_TIMEOUT_SECONDS)
    except requests.RequestException as exc:
        logger.warning("HF NER request failed: %s", exc)
        return []

    if resp.status_code != 200:
        logger.warning("HF NER call returned %s: %s", resp.status_code, resp.text[:200])
        return []

    data = resp.json()
    if not isinstance(data, list):
        # e.g. {"error": "Model ... is currently loading", "estimated_time": ...}
        logger.warning("HF NER call returned non-list payload: %s", str(data)[:200])
        return []
    return data


def extract_location_text(message: str) -> Optional[str]:
    """Return the best-guess location span mentioned in `message`, or None
    if no location entity was found (or the call failed)."""
    entities = _call_ner(message)
    loc_entities = [e for e in entities if _clean_label(e) == "LOC"]
    if not loc_entities:
        return None

    spans_with_offsets = [
        (e["start"], e["end"]) for e in loc_entities if e.get("start") is not None and e.get("end") is not None
    ]
    if not spans_with_offsets:
        best = max(loc_entities, key=lambda e: e.get("score", 0))
        word = best.get("word")
        return word.strip() if word else None

    # Merge adjacent/overlapping spans (e.g. "New" + "York") into one.
    spans_with_offsets.sort()
    merged = [spans_with_offsets[0]]
    for start, end in spans_with_offsets[1:]:
        if start - merged[-1][1] <= 1:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))

    best_span = max(merged, key=lambda s: s[1] - s[0])
    text = message[best_span[0]:best_span[1]].strip()
    return text or None
