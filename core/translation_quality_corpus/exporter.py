from __future__ import annotations

from .model import GoldenReviewCase
from .validator import validate_golden_cases


def corpus_payload(cases: tuple[GoldenReviewCase, ...]) -> dict[str, object]:
    rows = validate_golden_cases(cases)
    return {"corpus": "te_v71_initial_defects", "human_review_only": True, "cases": [row.to_dict() for row in rows]}
