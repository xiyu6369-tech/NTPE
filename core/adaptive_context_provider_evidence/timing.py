from __future__ import annotations

from datetime import datetime, timezone
from typing import Mapping


def normalize_utc(value: object) -> str:
    text = str(value or "").strip()
    if text:
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return ""
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    return ""


def request_elapsed_ms(result: Mapping[str, object]) -> float | None:
    raw_ms = result.get("provider_elapsed_ms")
    raw_seconds = result.get("provider_elapsed_seconds")
    try:
        value = float(raw_ms) if raw_ms is not None else float(raw_seconds) * 1000 if raw_seconds is not None else None
    except (TypeError, ValueError):
        return None
    return round(value, 3) if value is not None and value >= 0 else None
