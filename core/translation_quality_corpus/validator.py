from __future__ import annotations

from collections.abc import Iterable

from core.translation_quality_defects import validate_category, validate_severity

from .model import GoldenReviewCase


def validate_golden_cases(cases: Iterable[GoldenReviewCase]) -> tuple[GoldenReviewCase, ...]:
    rows = tuple(cases)
    ids = [row.case_id for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate golden review case id")
    for row in rows:
        if not row.human_confirmed:
            raise ValueError("unreviewed case cannot enter golden corpus")
        if row.approved_final_translation is not None:
            raise ValueError("approved final translation must remain null")
        if not row.preferred_direction.strip():
            raise ValueError("preferred direction is required")
        validate_severity(row.severity)
        for category in row.categories:
            validate_category(category)
    return rows
