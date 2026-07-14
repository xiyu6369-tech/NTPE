from __future__ import annotations

from collections.abc import Iterable

from .categories import validate_category
from .model import TranslationDefect
from .severity import validate_severity

MAX_EXCERPT_CHARS = 80


def validate_defect(defect: TranslationDefect) -> TranslationDefect:
    if not defect.defect_id.startswith("TQ-"):
        raise ValueError("defect id must use TQ- prefix")
    validate_category(defect.category)
    if defect.category in defect.secondary_categories:
        raise ValueError("primary category cannot repeat as secondary")
    if len(set(defect.secondary_categories)) != len(defect.secondary_categories):
        raise ValueError("duplicate secondary category")
    for category in defect.secondary_categories:
        validate_category(category)
    validate_severity(defect.severity)
    for excerpt in (defect.source_excerpt, defect.translation_excerpt):
        if excerpt is not None and len(excerpt) > MAX_EXCERPT_CHARS:
            raise ValueError("defect excerpt exceeds minimal-evidence limit")
    if not 0.0 <= defect.confidence <= 1.0:
        raise ValueError("confidence must be between zero and one")
    if defect.blocking and defect.severity != "critical":
        raise ValueError("only critical defects may block quality approval")
    if defect.metadata.get("approved_translation") is not None:
        raise ValueError("suggestions cannot be marked as approved translations")
    return defect


def validate_defects(defects: Iterable[TranslationDefect]) -> tuple[TranslationDefect, ...]:
    rows = tuple(validate_defect(row) for row in defects)
    ids = [row.defect_id for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate defect id")
    return rows
