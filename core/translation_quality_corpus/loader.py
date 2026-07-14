from __future__ import annotations

import json
from pathlib import Path

from .integrity import corpus_sha256
from .model import GoldenReviewCase
from .validator import validate_golden_cases


def load_golden_corpus(path: str | Path) -> tuple[GoldenReviewCase, ...]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    integrity = payload.pop("integrity", {})
    if integrity.get("payload_sha256") != corpus_sha256(payload):
        raise ValueError("golden corpus integrity failure")
    return validate_golden_cases(GoldenReviewCase(**row) for row in payload["cases"])
